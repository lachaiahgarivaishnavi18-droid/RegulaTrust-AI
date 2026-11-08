import io
import json
from html import escape
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def safe_cell(value):
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value if value is not None else '')
    return "'" + text if text.startswith(('=', '+', '-', '@', '\t', '\r')) else text


def export_report(report, format):
    snapshot = report.snapshot
    checks = snapshot['compliance']['validations']
    if report.kind == 'Exception report':
        checks = [item for item in checks if item['status'] != 'Compliant' or item['evidence']['check_outcome'] != 'Passed']
    sections = []
    if report.kind in ('Regulatory compliance report', 'Exception report'):
        sections.append(('Validations', checks))
    if report.kind in ('Regulatory compliance report', 'Exception report', 'Data quality report'):
        sections.append(('Quality', snapshot['quality']['issues']))
    if report.kind in ('Regulatory compliance report', 'Exception report', 'Anomaly report'):
        sections.append(('Anomalies', snapshot['anomalies']['anomalies']))
    sections.append(('Sources', snapshot['sources']))
    buffer = io.BytesIO()
    if format == 'xlsx':
        book = Workbook()
        sheet = book.active
        sheet.title = 'Summary'
        for key, value in {'report_id': report.id, 'status': report.status, 'version': report.version, 'kind': report.kind, 'notice': snapshot['notice'], 'document_sha256': snapshot['document_sha256'], 'dataset_hash': snapshot['dataset_hash'], 'record_count': snapshot['record_count'], 'risk': snapshot['risk'], 'quality_score': snapshot['quality']['score']}.items():
            sheet.append([key, safe_cell(value)])
        for title, rows in sections:
            tab = book.create_sheet(title)
            if rows:
                headers = list(rows[0])
                tab.append(headers)
                for row in rows:
                    tab.append([safe_cell(row.get(h)) for h in headers])
            tab.freeze_panes = 'A2'
            tab.auto_filter.ref = tab.dimensions
        for tab in book:
            for column in tab.columns:
                tab.column_dimensions[column[0].column_letter].width = 28
        book.save(buffer)
        return buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    styles = getSampleStyleSheet()
    story = [Paragraph('RegulaTrust | ' + escape(report.kind), styles['Title']), Spacer(1, 12)]
    def paragraph(text, style='BodyText'):
        story.append(Paragraph(escape(str(text)), styles[style]))
        story.append(Spacer(1, 6))
    for text in [snapshot['notice'], f'Report: {report.id} | Version: {report.version} | Status: {report.status}', f"Document SHA-256: {snapshot['document_sha256']}", f"Records: {snapshot['record_count']} | Data quality: {snapshot['quality']['score']}%", f"Risk: {snapshot['risk']['score']} / 100 ({snapshot['risk']['category']})", snapshot['risk']['formula']]:
        paragraph(text)
    paragraph('Recommended actions', 'Heading2')
    for action in snapshot['risk']['recommendations']:
        paragraph(action)
    for title, rows in sections:
        paragraph(title, 'Heading2')
        if not rows:
            paragraph('No items in this section within the evaluated scope.')
        for item in rows:
            if title == 'Validations':
                paragraph(f"Row {item['row']} | {item['status']} | {item['severity']} | {item['explanation']}")
                paragraph(json.dumps(item['evidence']))
                paragraph(item['recommendation'])
            elif title == 'Anomalies':
                paragraph(item['explanation'] + ' Evidence: ' + json.dumps(item['evidence']))
            elif title == 'Sources':
                paragraph(f"{item['title']} | {item['version']} | Verified: {item['verified']} | {item['source_url'] or 'No authoritative URL supplied'}")
            else:
                paragraph(json.dumps(item))
    SimpleDocTemplate(buffer, pagesize=A4, title='RegulaTrust regulatory report').build(story)
    return buffer.getvalue(), 'application/pdf'
