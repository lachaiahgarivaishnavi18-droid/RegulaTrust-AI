import io
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import select
from app.models import AgentExecution, BankingRecord, User, UploadedDocument
from app.main import rates

PASSWORD='Strong-test-password-123'


def add_reviewer(client, account, role='Compliance Officer', email='reviewer@example.com'):
    created=client.post('/api/users',headers=account,json={'name':'Independent Reviewer','email':email,'password':PASSWORD,'organization':'ignored','role':role})
    assert created.status_code==201, created.text
    response=client.post('/api/auth/login',json={'email':email,'password':PASSWORD})
    return {'Authorization':'Bearer '+response.json()['access_token']}


def seed_and_run(client, account):
    seed=client.post('/api/demo/seed',headers=account)
    assert seed.status_code==201,seed.text
    response=client.post('/api/agents/run',headers=account,json={'document_id':seed.json()['id']})
    assert response.status_code==200,response.text
    return seed.json(),response.json()


def test_auth_login_logout_and_expiry(client,account):
    assert client.get('/api/auth/me').status_code==401
    assert client.get('/api/auth/me',headers=account).json()['roles']==['Administrator']
    assert client.post('/api/auth/login',json={'email':'admin@example.com','password':'wrong'}).status_code==401
    assert client.post('/api/auth/logout',headers=account).status_code==200
    assert client.get('/api/auth/me',headers=account).status_code==401


def test_registration_and_tenant_isolation(client,account):
    doc=client.post('/api/demo/seed',headers=account).json()
    response=client.post('/api/auth/register',json={'name':'Other','organization':'Other Bank','email':'other@example.com','password':PASSWORD})
    other={'Authorization':'Bearer '+response.json()['access_token']}
    assert client.get('/api/documents',headers=other).json()==[]
    assert client.get('/api/documents/'+doc['id'],headers=other).status_code==404
    assert client.post('/api/agents/run',headers=other,json={'document_id':doc['id']}).status_code==404
    assert client.get('/api/audit-logs',headers=other).json()[0]['action']=='account.registered'
    assert client.post('/api/auth/register',json={'name':'N','organization':'O','email':'bad','password':'short'}).status_code==422


def test_workflow_exports_and_demo_review(client,account,db_factory):
    doc,run=seed_and_run(client,account)
    executions=client.get('/api/agents/executions?run_id='+run['run_id'],headers=account).json()
    assert len(executions)==8
    assert all(e['progress']==100 for e in executions)
    checks=client.get('/api/compliance/results',headers=account).json()
    assert len(checks)==96
    assert all(c['status']=='Needs Review' for c in checks)
    assert all(c['evidence']['document_sha256']==doc['sha256'] for c in checks)
    assert client.get('/api/dashboard/summary',headers=account).json()['compliance_score'] is None
    assert client.get('/api/anomalies',headers=account).json()
    assert client.get('/api/risks',headers=account).json()[0]['score']>0
    for fmt in ['pdf','xlsx']:
        export=client.get(f"/api/reports/{run['report_id']}/download?format={fmt}",headers=account)
        assert export.status_code==200
        if fmt=='pdf':assert len(PdfReader(io.BytesIO(export.content)).pages)>0
        else:assert 'Validations' in load_workbook(io.BytesIO(export.content)).sheetnames
    assert client.post(f"/api/approvals/{run['report_id']}/approve",headers=account,json={'version':1,'comment':'Reviewed independently'}).status_code==403
    reviewer=add_reviewer(client,account)
    assert client.post(f"/api/approvals/{run['report_id']}/approve",headers=reviewer,json={'version':1,'comment':'Reviewed independently'}).status_code==409
    assert client.post(f"/api/approvals/{run['report_id']}/reject",headers=reviewer,json={'version':1,'comment':'Sources require verification'}).status_code==200
    assert client.get('/api/reports/'+run['report_id'],headers=reviewer).json()['approvals'][0]['decision']=='Rejected'
    second=client.post('/api/agents/run',headers=account,json={'document_id':doc['id']})
    assert second.status_code==200
    assert len(client.get('/api/compliance/results',headers=account).json())==96
    assert client.get('/api/dashboard/summary',headers=account).json()['reports_processed']==1
    # Database state survives a new ORM session.
    with db_factory() as db:
        assert len(db.scalars(select(BankingRecord)).all())==32
        assert len(db.scalars(select(AgentExecution)).all())==16


def test_auditor_denied_writes(client,account):
    auditor=add_reviewer(client,account,'Auditor','audit@example.com')
    assert client.post('/api/demo/seed',headers=auditor).status_code==403
    assert client.get('/api/users',headers=auditor).status_code==403
    assert client.post('/api/frameworks',headers=auditor,json={'name':'Bad','jurisdiction':'Test'}).status_code==403
    assert client.get('/api/dashboard/summary',headers=auditor).status_code==200


def test_upload_validation_and_masking(client,account):
    assert client.post('/api/documents/upload',headers=account,files={'file':('bad.exe',b'bad')}).status_code==422
    assert client.post('/api/documents/upload',headers=account,files={'file':('bad.csv',b'account_id,loan_exposure\n123456,100')},data={'mapping':'[]'}).status_code==422
    result=client.post('/api/documents/upload',headers=account,files={'file':('../../private.csv',b'account_id,loan_exposure\n123456,100')})
    assert result.status_code==201,result.text
    assert result.json()['filename']=='private.csv'
    assert result.json()['preview'][0]['account_id']=='***3456'
    assert 'storage_path' not in result.json()
    assert client.post('/api/documents/upload',headers=account,files={'file':('huge.csv',b'x'*(10*1024*1024+1))}).status_code==413


def test_verified_approval_happy_path(client,account):
    framework=client.post('/api/frameworks',headers=account,json={'name':'Synthetic integration test control','jurisdiction':'Test only','enabled':True}).json()
    source=client.post('/api/knowledge/sources',headers=account,json={'framework_id':framework['id'],'title':'Synthetic test source — no legal authority','source_url':'https://example.com/test-only','version':'test-1','text':'Synthetic control: loan exposures must be at least zero for this test.','verified':True}).json()
    rule=client.post('/api/rules',headers=account,json={'framework_id':framework['id'],'source_id':source['id'],'code':'TEST-EXP','version':'1','clause':'Synthetic test clause','field':'loan_exposure','operator':'gte','threshold':'0','severity':'Medium','verified':True,'corrective_action':'Reconcile exposure'})
    assert rule.status_code==201,rule.text
    csv=b'customer_id,account_id,reporting_date,capital,risk_weighted_assets,loan_exposure,kyc_status\nC001,A001,2026-09-30,100,1000,500,complete'
    doc=client.post('/api/documents/upload',headers=account,files={'file':('test.csv',csv)}).json()
    report=client.post('/api/agents/run',headers=account,json={'document_id':doc['id']}).json()
    reviewer=add_reviewer(client,account)
    result=client.post('/api/approvals/'+report['report_id']+'/approve',headers=reviewer,json={'version':1,'comment':'Synthetic integration test independently reviewed'})
    assert result.status_code==200,result.text
    assert result.json()['status']=='Approved'
    assert client.post('/api/approvals/'+report['report_id']+'/approve',headers=reviewer,json={'version':1,'comment':'Second attempt'}).status_code==409
    assert client.get('/api/dashboard/summary',headers=account).json()['compliance_score']==100
    assert client.get('/api/knowledge/search?q=exposures',headers=account).json()[0]['id']==source['id']


def test_agent_failure_records_history(client,account,monkeypatch):
    from app.orchestration import HANDLERS
    def fail(_):raise RuntimeError('sensitive error must not leak')
    monkeypatch.setitem(dict(), 'unused', 1)
    original=HANDLERS[1]
    HANDLERS[1]=fail
    try:
        doc=client.post('/api/demo/seed',headers=account).json()
        response=client.post('/api/agents/run',headers=account,json={'document_id':doc['id']})
        assert response.status_code==500
        assert 'sensitive' not in response.text
        executions=client.get('/api/agents/executions',headers=account).json()
        failed=[e for e in executions if e['status']=='Failed']
        assert len(failed)==1
        assert failed[0]['attempts']==2
        assert client.get('/api/reports',headers=account).json()==[]
    finally:
        HANDLERS[1]=original


def test_rate_limit_and_headers(client):
    for _ in range(15):
        client.post('/api/auth/login',json={'email':'absent@example.com','password':'wrong'})
    result=client.post('/api/auth/login',json={'email':'absent@example.com','password':'wrong'})
    assert result.status_code==429
    assert result.headers['retry-after']=='60'
    health=client.get('/health')
    assert health.headers['x-content-type-options']=='nosniff'
