"""Deterministic modular agents. Only the optional narrative provider uses an LLM."""
import hashlib
import json
import statistics
from datetime import date
from .ingestion import quality, numeric

AGENTS = [
    ('Data Ingestion', 'Normalize records and preserve document provenance'),
    ('Data Quality', 'Validate completeness, types, duplicates and reporting dates'),
    ('Regulatory Knowledge', 'Retrieve configured, versioned regulatory requirements'),
    ('Compliance Validation', 'Evaluate deterministic controls with traceable evidence'),
    ('Anomaly Detection', 'Compare exposures using robust statistics and historical changes'),
    ('Risk Assessment', 'Calculate transparent weighted risk and corrective actions'),
    ('Regulatory Reporting', 'Create immutable evidence-backed report snapshots'),
    ('Explainability & Audit', 'Record execution lineage and human review requirements'),
]


def ingestion_agent(context):
    rows = context['rows']
    canonical = json.dumps(rows, sort_keys=True, separators=(',', ':'))
    return {'records': len(rows), 'dataset_hash': hashlib.sha256(canonical.encode()).hexdigest(), 'document_sha256': context['document_sha256'], 'normalization_version': '1.0.0'}


def quality_agent(context):
    return quality(context['rows'])


def knowledge_agent(context):
    return {'rules': context['rules'], 'sources': context['sources'], 'applicability': 'Only explicitly enabled frameworks in this organization', 'verification_required': any(not rule['verified'] for rule in context['rules']) or not context['rules']}


def validate_rule(row, rule):
    value = row.get(rule['field'])
    if rule['field'] == 'capital_ratio':
        capital, rwa = numeric(row.get('capital')), numeric(row.get('risk_weighted_assets'))
        value = capital / rwa if capital is not None and capital >= 0 and rwa is not None and rwa > 0 else None
    valid = value is not None
    passed = False
    if rule['operator'] in ('gte', 'lte'):
        number, threshold = numeric(value), numeric(rule['threshold'])
        valid = number is not None and threshold is not None
        passed = valid and (number >= threshold if rule['operator'] == 'gte' else number <= threshold)
    elif rule['operator'] == 'eq':
        passed = valid and str(value).casefold() == rule['threshold'].casefold()
    elif rule['operator'] == 'required':
        passed = valid and str(value).strip() != ''
    else:
        valid = False
    # Unverified demo controls can detect a failed check, but never certify compliance.
    status = ('Compliant' if passed else 'Non-Compliant') if rule['verified'] and valid else 'Needs Review'
    outcome = 'Passed' if passed else 'Failed' if valid else 'Indeterminate'
    return {'status': status, 'severity': 'Low' if passed else rule['severity'], 'evidence': {'field': rule['field'], 'observed': value, 'operator': rule['operator'], 'threshold': rule['threshold'], 'check_outcome': outcome, 'rule_code': rule['code'], 'rule_version': rule['version'], 'clause': rule['clause'], 'source': rule['source'], 'verified_source': rule['verified']}, 'explanation': f"{rule['code']} {rule['version']}: {outcome.lower()}; observed {value!r}, expected {rule['operator']} {rule['threshold']}." + (' Source verification required.' if not rule['verified'] else ''), 'recommendation': rule['corrective_action'] if not passed else 'Retain evidence and obtain human review.'}


def compliance_agent(context):
    results = []
    for index, row in enumerate(context['rows']):
        for rule in context['rules']:
            result = validate_rule(row, rule)
            result.update({'row': index + 1, 'rule_id': rule['id'], 'record_id': context['record_ids'][index]})
            result['evidence'].update({'row': index + 1, 'document_sha256': context['document_sha256']})
            results.append(result)
    return {'validations': results, 'rule_count': len(context['rules']), 'requires_review': not results or any(r['status'] == 'Needs Review' for r in results)}


def anomaly_agent(context):
    pairs = [(i, numeric(r.get('loan_exposure'))) for i, r in enumerate(context['rows'])]
    pairs = [(i, v) for i, v in pairs if v is not None and v >= 0]
    values = [v for _, v in pairs]
    median = statistics.median(values) if values else 0
    mad = statistics.median([abs(v - median) for v in values]) if values else 0
    anomalies = []
    for index, value in pairs:
        distance = abs(value - median)
        score = .6745 * distance / mad if mad else (distance / max(abs(median), 1))
        if len(values) >= 5 and score > 3.5:
            anomalies.append({'record_id': context['record_ids'][index], 'score': round(min(100, score * 10), 2), 'category': 'High' if score > 7 else 'Medium', 'explanation': f'Loan exposure {value:g} differs from median {median:g}; robust deviation {score:.2f}. This is a review signal, not evidence of misconduct.', 'evidence': {'row': index + 1, 'value': value, 'median': median, 'mad': mad, 'method': 'modified-z-score-v1', 'threshold': 3.5}})
    # Compare each account with its most recent prior date, including prior uploaded data.
    history = context.get('history', []) + context['rows']
    for index, row in enumerate(context['rows']):
        try:
            current_date = date.fromisoformat(row.get('reporting_date', ''))
        except (ValueError, TypeError):
            continue
        prior = []
        for old in history:
            try:
                old_date = date.fromisoformat(old.get('reporting_date', ''))
                old_value = numeric(old.get('loan_exposure'))
                if old.get('account_id') == row.get('account_id') and old_date < current_date and old_value is not None and old_value > 0:
                    prior.append((old_date, old_value))
            except (ValueError, TypeError):
                continue
        value = numeric(row.get('loan_exposure'))
        if prior and value is not None:
            old_date, old_value = max(prior)
            change = (value - old_value) / old_value
            if abs(change) > 1:
                anomalies.append({'record_id': context['record_ids'][index], 'score': round(min(100, abs(change) * 25), 2), 'category': 'High', 'explanation': f'Exposure changed {change:.1%} compared with {old_date.isoformat()}. Reconcile the movement.', 'evidence': {'row': index + 1, 'current': value, 'previous': old_value, 'previous_date': old_date.isoformat(), 'change': change, 'method': 'prior-period-change-v1'}})
    return {'anomalies': anomalies, 'records_evaluated': len(values), 'method': 'modified-z-score-v1 + prior-period-change-v1', 'limitations': 'Small datasets (<5 numeric observations) skip cross-sectional detection; absent history prevents historical comparison.'}


def risk_agent(context):
    validations = context['outputs']['Compliance Validation']['validations']
    weights = {'Critical': 10, 'High': 6, 'Medium': 3, 'Low': 1}
    failed = [v for v in validations if v['evidence']['check_outcome'] != 'Passed']
    denominator = sum(weights[r['severity']] for r in context['rules']) * len(context['rows'])
    regulatory = 100 * sum(weights[v['severity']] for v in failed) / max(1, denominator)
    quality_risk = 100 - context['outputs']['Data Quality']['score']
    anomalies = context['outputs']['Anomaly Detection']['anomalies']
    reporting = min(100, len({a['record_id'] for a in anomalies}) / max(1, len(context['rows'])) * 100)
    uncertainty = 100 if not context['rules'] else 100 * sum(not r['verified'] for r in context['rules']) / len(context['rules'])
    score = round(.45 * regulatory + .25 * quality_risk + .15 * reporting + .15 * uncertainty, 2)
    category = 'Critical' if score >= 75 else 'High' if score >= 50 else 'Medium' if score >= 25 else 'Low'
    return {'score': score, 'category': category, 'components': {'regulatory': round(regulatory, 2), 'data_quality': round(quality_risk, 2), 'reporting': round(reporting, 2), 'source_uncertainty': round(uncertainty, 2)}, 'formula': '0.45 regulatory + 0.25 data quality + 0.15 reporting + 0.15 source uncertainty', 'recommendations': sorted(set(v['recommendation'] for v in failed)) + (['Verify regulatory sources and applicability before approval.'] if uncertainty else [])}


def reporting_agent(context):
    return {'document_sha256': context['document_sha256'], 'dataset_hash': context['outputs']['Data Ingestion']['dataset_hash'], 'demo': context['demo'], 'record_count': len(context['rows']), 'quality': context['outputs']['Data Quality'], 'compliance': context['outputs']['Compliance Validation'], 'anomalies': context['outputs']['Anomaly Detection'], 'risk': context['outputs']['Risk Assessment'], 'sources': context['sources'], 'rules': context['rules'], 'approval_required': True, 'notice': 'DEMO DATA — not bank compliance certification.' if context['demo'] else 'Validation scope is limited to configured controls; human approval is mandatory.'}


def audit_agent(context):
    return {'run_id': context['run_id'], 'document_sha256': context['document_sha256'], 'agent_version': '1.0.0', 'rule_versions': {r['code']: r['version'] for r in context['rules']}, 'stages': list(context['outputs']), 'human_review_required': True, 'llm_used_for_decisions': False, 'confidence': 'Deterministic check confidence; source authority is separately recorded, not inferred.'}


HANDLERS = [ingestion_agent, quality_agent, knowledge_agent, compliance_agent, anomaly_agent, risk_agent, reporting_agent, audit_agent]
