import csv
import io
import json
import math
import zipfile
from datetime import date, datetime
from openpyxl import load_workbook
from pypdf import PdfReader

FIELDS = ['customer_id', 'account_id', 'reporting_date', 'capital', 'risk_weighted_assets', 'loan_exposure', 'kyc_status']
NUMERIC = ['capital', 'risk_weighted_assets', 'loan_exposure']
MAX_ROWS = 20000


def normalize(rows, mapping):
    result = []
    for row in rows:
        cleaned = {}
        for key, value in row.items():
            key = str(key).strip().lower().replace(' ', '_')
            key = mapping.get(key, key)
            if isinstance(value, (date, datetime)):
                value = value.isoformat()[:10]
            if value is not None:
                value = str(value).strip()
            cleaned[key] = value or None
        result.append(cleaned)
        if len(result) > MAX_ROWS:
            raise ValueError(f'At most {MAX_ROWS} records are supported')
    if not result:
        raise ValueError('No data rows found')
    if not any(field in result[0] for field in FIELDS):
        raise ValueError('No recognized banking columns. Supply a column mapping.')
    return result


def parse_file(filename, content, mapping=None):
    mapping = mapping or {}
    extension = filename.rsplit('.', 1)[-1].lower()
    if extension == 'csv':
        text = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('CSV headers must be unique')
        rows = list(reader)
    elif extension == 'xlsx':
        if not content.startswith(b'PK'):
            raise ValueError('Invalid XLSX signature')
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if sum(f.file_size for f in archive.infolist()) > 50 * 1024 * 1024:
                raise ValueError('Expanded workbook exceeds 50 MB')
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=False)
        sheet = workbook.active
        if sheet.max_row > MAX_ROWS + 1 or sheet.max_column > 100:
            raise ValueError('Workbook exceeds row or column limits')
        values = sheet.iter_rows(values_only=True)
        headers = next(values, ())
        if not headers or len(headers) != len(set(headers)):
            raise ValueError('Workbook headers must be unique')
        rows = []
        for row in values:
            if any(isinstance(v, str) and v.startswith('=') for v in row):
                raise ValueError('Formula cells are not accepted; export values first')
            rows.append(dict(zip(headers, row)))
        workbook.close()
    elif extension == 'pdf':
        if not content.startswith(b'%PDF-'):
            raise ValueError('Invalid PDF signature')
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted or len(reader.pages) > 100:
            raise ValueError('Encrypted PDFs or PDFs above 100 pages are not supported')
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        # Structured, text-based PDFs use CSV-formatted rows. Never guess financial values.
        lines = [line for line in text.splitlines() if ',' in line]
        if not lines:
            raise ValueError('PDF has no structured CSV table. Upload text-based CSV-table PDF or CSV/XLSX; scanned PDFs require manual extraction.')
        rows = list(csv.DictReader(io.StringIO('\n'.join(lines))))
    else:
        raise ValueError('Supported formats: CSV, XLSX, text-based PDF')
    return normalize(rows, mapping)


def numeric(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def quality(rows):
    issues, seen = [], set()
    for index, row in enumerate(rows, 1):
        for field in FIELDS:
            if row.get(field) is None:
                issues.append({'row': index, 'field': field, 'issue': 'Missing required value'})
        for field in NUMERIC:
            value = numeric(row.get(field))
            if row.get(field) is not None and (value is None or value < 0):
                issues.append({'row': index, 'field': field, 'issue': 'Expected a finite non-negative number'})
        if numeric(row.get('risk_weighted_assets')) == 0:
            issues.append({'row': index, 'field': 'risk_weighted_assets', 'issue': 'Risk-weighted assets must be greater than zero'})
        try:
            date.fromisoformat(row.get('reporting_date') or '')
        except ValueError:
            issues.append({'row': index, 'field': 'reporting_date', 'issue': 'Expected ISO date YYYY-MM-DD'})
        key = (row.get('account_id'), row.get('reporting_date'))
        if key in seen:
            issues.append({'row': index, 'field': 'account_id', 'issue': 'Duplicate account and reporting date'})
        seen.add(key)
    periods = sorted({r.get('reporting_date') for r in rows if r.get('reporting_date')})
    invalid_cells = {(i['row'], i['field']) for i in issues}
    return {'score': round(max(0, 100 * (1 - len(invalid_cells) / max(1, len(rows) * len(FIELDS)))), 2), 'issues': issues, 'periods': periods}
