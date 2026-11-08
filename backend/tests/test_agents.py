import io
from openpyxl import Workbook
import pytest
from app.agents import validate_rule, anomaly_agent, risk_agent
from app.ingestion import parse_file, quality
from app.knowledge import embed
from app.exports import safe_cell


def rule(verified=True):
    return {'field':'capital_ratio','operator':'gte','threshold':'0.1','verified':verified,'severity':'Critical','code':'TEST-CAP','version':'1','clause':'Synthetic test control','source':{'version':'1'},'corrective_action':'Reconcile capital'}


@pytest.mark.parametrize('capital,rwa,status', [('120', '1000','Compliant'),('90','1000','Non-Compliant'),('10','0','Needs Review'),('NaN','100','Needs Review'),('-10','100','Needs Review'),(None,'100','Needs Review')])
def test_capital_rule(capital,rwa,status):
    result = validate_rule({'capital':capital,'risk_weighted_assets':rwa},rule())
    assert result['status'] == status


def test_demo_never_certifies():
    result=validate_rule({'capital':'120','risk_weighted_assets':'1000'},rule(False))
    assert result['status']=='Needs Review'
    assert result['evidence']['check_outcome']=='Passed'


def test_formats_and_quality():
    rows=parse_file('test.csv',b'customer_id,account_id,reporting_date,capital,risk_weighted_assets,loan_exposure,kyc_status\nC1,A1,2026-09-30,10,100,20,complete\nC1,A1,bad,,0,NaN,pending')
    result=quality(rows)
    assert result['score']<100
    assert any(i['field']=='reporting_date' for i in result['issues'])
    assert any(i['field']=='loan_exposure' for i in result['issues'])
    with pytest.raises(ValueError): parse_file('bad.exe',b'hello')
    with pytest.raises(ValueError): parse_file('bad.csv',b'a,a\n1,2')
    with pytest.raises(ValueError): parse_file('bad.pdf',b'not a PDF')


def test_xlsx_and_formula_rejection():
    workbook=Workbook();sheet=workbook.active
    sheet.append(['account_id','loan_exposure']);sheet.append(['A1',100])
    data=io.BytesIO();workbook.save(data)
    assert parse_file('data.xlsx',data.getvalue())[0]['loan_exposure']=='100'
    sheet.append(['A2','=1+2']);data=io.BytesIO();workbook.save(data)
    with pytest.raises(ValueError,match='Formula'):parse_file('data.xlsx',data.getvalue())


def test_anomaly_reproducibility_and_history():
    rows=[{'account_id':str(i),'reporting_date':'2026-09-30','loan_exposure':str(v)} for i,v in enumerate([100,102,98,101,99,10000])]
    context={'rows':rows,'record_ids':[str(i) for i in range(6)],'history':[{'account_id':'5','reporting_date':'2026-06-30','loan_exposure':'100'}]}
    result=anomaly_agent(context)
    assert result==anomaly_agent(context)
    assert any(a['record_id']=='5' for a in result['anomalies'])
    assert any(a['evidence']['method']=='prior-period-change-v1' for a in result['anomalies'])


def test_embeddings_and_excel_formula_safety():
    assert embed('capital adequacy')==embed('capital adequacy')
    assert sum(a*b for a,b in zip(embed('capital adequacy'),embed('capital adequacy'))) == pytest.approx(1)
    assert safe_cell('=HYPERLINK("evil")').startswith("'")


def test_structured_pdf_ingestion():
    from reportlab.pdfgen import canvas
    data=io.BytesIO()
    pdf=canvas.Canvas(data)
    pdf.drawString(30,780,'account_id,loan_exposure')
    pdf.drawString(30,760,'DEMO-A001,100')
    pdf.save()
    result=parse_file('synthetic.pdf',data.getvalue())
    assert result[0]['account_id']=='DEMO-A001'
    assert result[0]['loan_exposure']=='100'
