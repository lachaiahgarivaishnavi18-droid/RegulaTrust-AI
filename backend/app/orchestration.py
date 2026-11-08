import time
import json
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from .models import *
from .agents import AGENTS, HANDLERS
from .knowledge import search


def run_pipeline(db: Session, user: User, document_id: str):
    doc = db.scalar(select(UploadedDocument).where(UploadedDocument.id == document_id, UploadedDocument.organization_id == user.organization_id))
    if not doc:
        raise ValueError('Document not found')
    acquired = db.execute(update(UploadedDocument).where(UploadedDocument.id == doc.id, UploadedDocument.status != 'Running').values(status='Running'))
    if acquired.rowcount != 1:
        raise ValueError('Document already processing')
    db.commit()
    org = user.organization_id
    run_id = uid()
    executions = []
    for name, _ in AGENTS:
        execution = AgentExecution(organization_id=org, document_id=doc.id, run_id=run_id, agent=name, status='Pending')
        db.add(execution)
        executions.append(execution)
    db.commit()
    try:
        records = db.scalars(select(BankingRecord).where(BankingRecord.document_id == doc.id, BankingRecord.organization_id == org).order_by(BankingRecord.row_number)).all()
        query = select(RegulatoryRule).join(RegulatoryFramework, RegulatoryFramework.id == RegulatoryRule.framework_id).where(RegulatoryRule.organization_id == org, RegulatoryFramework.organization_id == org, RegulatoryFramework.enabled.is_(True))
        if not doc.demo:
            query = query.where(RegulatoryFramework.name != 'Illustrative DEMO controls')
        candidates = db.scalars(query.order_by(RegulatoryRule.created_at.desc(), RegulatoryRule.id)).all()
        latest_rules = {}
        for rule in candidates:
            latest_rules.setdefault((rule.framework_id, rule.code), rule)
        rules = sorted(latest_rules.values(), key=lambda r: (r.code, r.id))
        sources = search(db, org, 'capital adequacy loan exposure KYC reporting')
        serialized_rules = []
        for rule in rules:
            source = db.get(RegulatoryDocument, rule.source_id) if rule.source_id else None
            framework = db.get(RegulatoryFramework, rule.framework_id)
            source_valid = source and source.organization_id == org and source.framework_id == rule.framework_id and source.verified and source.source_url.startswith('https://')
            serialized_rules.append({'id': rule.id, 'code': rule.code, 'version': rule.version, 'clause': rule.clause, 'field': rule.field, 'operator': rule.operator, 'threshold': rule.threshold, 'severity': rule.severity, 'corrective_action': rule.corrective_action, 'verified': bool(rule.verified and source_valid), 'framework': framework.name, 'source': {'id': source.id, 'url': source.source_url, 'version': source.version, 'title': source.title} if source else None})
        history = db.scalars(select(BankingRecord).where(BankingRecord.organization_id == org, BankingRecord.document_id != doc.id).order_by(BankingRecord.created_at, BankingRecord.row_number)).all()
        context = {'run_id': run_id, 'rows': [r.data for r in records], 'record_ids': [r.id for r in records], 'rules': serialized_rules, 'sources': sources, 'document_sha256': doc.sha256, 'demo': doc.demo, 'history': [r.data for r in history], 'outputs': {}}
        for execution, handler in zip(executions, HANDLERS):
            execution.status = 'Running'
            execution.progress = 10
            db.commit()
            start = time.perf_counter()
            for attempt in range(1, 3):
                execution.attempts = attempt
                try:
                    # Agents are pure functions; retries never duplicate persisted findings.
                    output = handler(context)
                    json.dumps(output, allow_nan=False)
                    break
                except Exception:
                    if attempt == 2:
                        raise
            execution.duration_ms = round((time.perf_counter() - start) * 1000, 2)
            execution.output = output
            execution.records_processed = len(records)
            execution.progress = 100
            execution.status = 'Requires Review' if execution.agent in ('Regulatory Reporting', 'Explainability & Audit') else 'Completed'
            context['outputs'][execution.agent] = output
            db.commit()
        # Persist the complete result set atomically after all agents succeed.
        db.add(DataQualityResult(organization_id=org, document_id=doc.id, **{k: context['outputs']['Data Quality'][k] for k in ('score', 'issues')}))
        for result in context['outputs']['Compliance Validation']['validations']:
            item = {k: v for k, v in result.items() if k != 'row'}
            validation = ComplianceValidation(organization_id=org, document_id=doc.id, run_id=run_id, **item)
            db.add(validation)
            db.flush()
            db.add(DocumentEvidence(organization_id=org, document_id=doc.id, validation_id=validation.id, sha256=doc.sha256, locator=f"row:{result['row']}"))
        for anomaly in context['outputs']['Anomaly Detection']['anomalies']:
            db.add(Anomaly(organization_id=org, document_id=doc.id, run_id=run_id, **anomaly))
        risk = context['outputs']['Risk Assessment']
        db.add(RiskAssessment(organization_id=org, document_id=doc.id, run_id=run_id, **{k: risk[k] for k in ('score', 'category', 'components', 'recommendations')}))
        report = RegulatoryReport(organization_id=org, document_id=doc.id, run_id=run_id, kind='Regulatory compliance report', snapshot=context['outputs']['Regulatory Reporting'])
        db.add(report)
        db.add(AuditLog(organization_id=org, user_id=user.id, action='pipeline.completed', details=context['outputs']['Explainability & Audit']))
        doc.status = 'Requires Review'
        db.commit()
        return {'run_id': run_id, 'report_id': report.id, 'status': doc.status}
    except Exception:
        failed_id = execution.id if 'execution' in locals() else None
        failed_attempts = attempt if 'attempt' in locals() else 0
        db.rollback()
        for execution in executions:
            if execution.id == failed_id and execution.status == 'Running':
                execution.status = 'Failed'
                execution.attempts = failed_attempts
                execution.error = 'Agent execution failed; contact administrator with run ID.'
        doc.status = 'Failed'
        db.add(AuditLog(organization_id=org, user_id=user.id, action='pipeline.failed', details={'run_id': run_id, 'document_id': doc.id}))
        db.commit()
        raise
