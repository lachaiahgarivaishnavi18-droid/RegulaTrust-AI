import io
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader


@pytest.mark.parametrize('kind,expected,excluded',[
    ('Data quality report','Quality','Validations'),
    ('Anomaly report','Anomalies','Quality'),
    ('Risk assessment report','Summary','Validations'),
    ('Executive summary','Summary','Anomalies'),
    ('Exception report','Validations',None),
])
def test_report_variants_export_scope(client,account,kind,expected,excluded):
    doc=client.post('/api/demo/seed',headers=account).json()
    assert client.post('/api/agents/run',headers=account,json={'document_id':doc['id']}).status_code==200
    response=client.post('/api/reports/generate',headers=account,json={'document_id':doc['id'],'kind':kind})
    assert response.status_code==201,response.text
    report=response.json()
    assert report['version']==2
    exported=client.get(f"/api/reports/{report['id']}/download?format=xlsx",headers=account)
    workbook=load_workbook(io.BytesIO(exported.content))
    assert expected in workbook.sheetnames
    if excluded:assert excluded not in workbook.sheetnames
    pdf=client.get(f"/api/reports/{report['id']}/download?format=pdf",headers=account)
    text=''.join(page.extract_text() for page in PdfReader(io.BytesIO(pdf.content)).pages)
    assert kind in text
    assert 'DEMO DATA' in text
