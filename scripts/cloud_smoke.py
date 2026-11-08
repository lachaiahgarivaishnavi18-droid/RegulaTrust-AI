"""Exercise the actual hosted workflow with explicitly synthetic data only."""
import hashlib
import io
import json
import secrets
from pathlib import Path
import httpx
from openpyxl import Workbook, load_workbook
from pypdf import PdfReader
from reportlab.pdfgen import canvas

root=Path(__file__).resolve().parents[1]
base='https://regulatrust-api.vercel.app'
frontend='https://regulatrust-ai.vercel.app'
credentials=root/'storage'/'config'/'cloud-smoke-user.json'
results={}


def expect(response,status=200):
    if response.status_code!=status:
        # Response bodies for failures can contain supplied authentication details.
        raise RuntimeError(f'{response.request.method} {response.request.url.path}: expected {status}, got {response.status_code}')
    return response


with httpx.Client(base_url=base,timeout=180) as client:
    expect(client.get('/ready'))
    results['api_ready']=True
    response=httpx.get(frontend,timeout=60)
    expect(response)
    assert 'RegulaTrust' in response.text
    results['frontend_served']=True
    preflight=client.options('/api/auth/login',headers={'Origin':frontend,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
    assert expect(preflight).headers.get('access-control-allow-origin')==frontend
    results['production_cors']=True
    if credentials.exists():
        account=json.loads(credentials.read_text(encoding='utf-8'))
        signed=expect(client.post('/api/auth/login',json={'email':account['email'],'password':account['password']})).json()
    else:
        tag=secrets.token_hex(5)
        account={'email':f'demo-cloud-{tag}@example.test','password':secrets.token_urlsafe(24),'name':'DEMO Cloud Verification','organization':'DEMO DATA — RegulaTrust Deployment Verification'}
        signed=expect(client.post('/api/auth/register',json=account),201).json()
        credentials.parent.mkdir(parents=True,exist_ok=True)
        credentials.write_text(json.dumps(account),encoding='utf-8')
    headers={'Authorization':'Bearer '+signed['access_token']}
    expect(client.get('/api/auth/me',headers=headers))
    expect(client.get('/api/documents'),401)
    results['authentication']=True
    documents=expect(client.get('/api/documents',headers=headers)).json()
    demo=next((d for d in documents if d['demo']),None)
    if not demo:
        demo=expect(client.post('/api/demo/seed',headers=headers),201).json()
    run=expect(client.post('/api/agents/run',headers=headers,json={'document_id':demo['id']})).json()
    executions=expect(client.get('/api/agents/executions',params={'run_id':run['run_id']},headers=headers)).json()
    assert len(executions)==8 and all(e['progress']==100 for e in executions)
    results['agents_completed']=8
    findings=expect(client.get('/api/compliance/results',headers=headers)).json()
    assert len(findings)==96 and all(f['status']=='Needs Review' for f in findings)
    assert all(f['evidence']['document_sha256']==demo['sha256'] for f in findings)
    results['evidence_backed_demo_validations']=96
    assert expect(client.get('/api/anomalies',headers=headers)).json()
    assert expect(client.get('/api/risks',headers=headers)).json()
    results['anomaly_and_risk']=True
    summary=expect(client.get('/api/dashboard/summary',headers=headers)).json()
    assert summary['reports_processed']>=1 and summary['compliance_score'] is None
    results['database_backed_dashboard']=True
    for kind in ['pdf','xlsx']:
        exported=expect(client.get(f"/api/reports/{run['report_id']}/download",params={'format':kind},headers=headers))
        if kind=='pdf':
            reader=PdfReader(io.BytesIO(exported.content))
            assert len(reader.pages)>0 and 'DEMO DATA' in reader.pages[0].extract_text()
        else:
            assert 'Validations' in load_workbook(io.BytesIO(exported.content)).sheetnames
        results[kind+'_export']=True
    csv_data=b'customer_id,account_id,reporting_date,capital,risk_weighted_assets,loan_exposure,kyc_status\nDEMO-C1001,DEMO-A1001,2026-09-30,150,1000,500,complete'
    workbook=Workbook();sheet=workbook.active
    sheet.append(['account_id','loan_exposure']);sheet.append(['DEMO-A1002',100])
    xlsx=io.BytesIO();workbook.save(xlsx)
    pdf=io.BytesIO();document=canvas.Canvas(pdf)
    document.drawString(30,780,'account_id,loan_exposure');document.drawString(30,760,'DEMO-A1003,100');document.save()
    uploaded=[]
    for filename,content in [('DEMO_cloud.csv',csv_data),('DEMO_cloud.xlsx',xlsx.getvalue()),('DEMO_cloud.pdf',pdf.getvalue())]:
        doc=expect(client.post('/api/documents/upload',headers=headers,files={'file':(filename,content)}),201).json()
        assert doc['sha256']==hashlib.sha256(content).hexdigest()
        assert 'source_bytes' not in doc
        uploaded.append(doc['id'])
    results['csv_xlsx_pdf_uploads']=True
    expect(client.post(f"/api/approvals/{run['report_id']}/approve",headers=headers,json={'version':1,'comment':'DEMO synthetic self-review must be denied'}),403)
    results['self_approval_denied']=True
    reviewer_email=account['email'].replace('demo-cloud-','demo-reviewer-')
    reviewer_password=account['password']
    created=client.post('/api/users',headers=headers,json={'name':'DEMO Independent Reviewer','email':reviewer_email,'password':reviewer_password,'organization':account['organization'],'role':'Compliance Officer'})
    assert created.status_code in (201,409)
    reviewer=expect(client.post('/api/auth/login',json={'email':reviewer_email,'password':reviewer_password})).json()
    reviewer_headers={'Authorization':'Bearer '+reviewer['access_token']}
    expect(client.post(f"/api/approvals/{run['report_id']}/approve",headers=reviewer_headers,json={'version':1,'comment':'DEMO unverified report must not be approved'}),409)
    expect(client.post(f"/api/approvals/{run['report_id']}/reject",headers=reviewer_headers,json={'version':1,'comment':'DEMO DATA: source verification and quality corrections required'}))
    decisions=expect(client.get('/api/reports/'+run['report_id'],headers=headers)).json()['approvals']
    assert decisions[-1]['decision']=='Rejected'
    results['independent_review_and_demo_approval_gate']=True
    audit=expect(client.get('/api/audit-logs',headers=headers)).json()
    assert any(a['action']=='report.rejected' for a in audit)
    results['audit_persistence']=True
    profile=expect(client.get('/api/settings',headers=headers)).json()
    assert profile['database']['dialect']=='postgresql'
    # A new session proves data is persisted beyond a single authenticated request.
    expect(client.post('/api/auth/logout',headers=headers))
    expect(client.get('/api/auth/me',headers=headers),401)
    signed_again=expect(client.post('/api/auth/login',json={'email':account['email'],'password':account['password']})).json()
    fresh={'Authorization':'Bearer '+signed_again['access_token']}
    assert len(expect(client.get('/api/documents',headers=fresh)).json())>=4
    results['logout_revocation_and_persistence']=True
    # Verify private originals directly in Neon without printing connection data or contents.
    import sys
    sys.path.insert(0,str(root/'backend'))
    from dotenv import dotenv_values
    from sqlalchemy import create_engine,select
    from sqlalchemy.orm import Session
    from app.models import UploadedDocument
    url=dotenv_values(root/'backend'/'.env')['DATABASE_URL'].replace('postgresql://','postgresql+psycopg://',1)
    engine=create_engine(url)
    with Session(engine) as db:
        stored=db.scalar(select(UploadedDocument).where(UploadedDocument.id==uploaded[0]))
        assert stored.storage_path=='database' and stored.source_bytes==csv_data
    engine.dispose()
    results['neon_private_original_persistence']=True

output=root/'docs'/'cloud-verification.json'
output.write_text(json.dumps({'date':'2026-11-08','frontend':frontend,'api':base,'synthetic_data_only':True,'checks':results},indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
