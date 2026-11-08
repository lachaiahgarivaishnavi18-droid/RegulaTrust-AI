import hashlib
import math
import re
from sqlalchemy import select
from .models import RegulatoryFramework, RegulatoryRule, RegulatoryDocument


def embed(text, dimensions=256):
    """Versioned local signed feature-hash embedding, no remote disclosure of data."""
    vector = [0.0] * dimensions
    for token in re.findall(r'[a-z0-9_]+', text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        vector[int.from_bytes(digest[:4], 'big') % dimensions] += 1 if digest[4] % 2 else -1
    norm = math.sqrt(sum(x*x for x in vector)) or 1
    return [x / norm for x in vector]


def search(db, org, query):
    vector = embed(query)
    documents = db.scalars(select(RegulatoryDocument).where(RegulatoryDocument.organization_id == org)).all()
    ranked = []
    for doc in documents:
        stored = doc.embedding or embed(doc.text)
        ranked.append({'id': doc.id, 'title': doc.title, 'source_url': doc.source_url, 'version': doc.version, 'verified': doc.verified, 'text': doc.text, 'similarity': round(sum(a*b for a, b in zip(vector, stored)), 4), 'embedding_model': 'sha256-feature-hash-256-v1'})
    return sorted(ranked, key=lambda d: d['similarity'], reverse=True)[:5]


def seed_demo_rules(db, org):
    existing = db.scalar(select(RegulatoryFramework).where(RegulatoryFramework.organization_id == org, RegulatoryFramework.name == 'Illustrative DEMO controls'))
    if existing:
        return existing
    framework = RegulatoryFramework(organization_id=org, name='Illustrative DEMO controls', jurisdiction='Synthetic sandbox', enabled=True)
    db.add(framework)
    db.flush()
    source = RegulatoryDocument(organization_id=org, framework_id=framework.id, title='DEMO control specification — not regulatory authority', source_url='', version='demo-1.0', verified=False, text='Illustrative capital adequacy floor 10%. KYC must be complete. Loan exposure non-negative. These are synthetic demonstration controls, not RBI, Basel III, IFRS 9 or AML legal requirements.')
    source.embedding = embed(source.text)
    db.add(source)
    db.flush()
    for code, field, operator, threshold, severity, clause, action in [
        ('DEMO-CAP-001', 'capital_ratio', 'gte', '0.10', 'Critical', 'Illustrative capital / risk-weighted assets >= 10%', 'Review capital and risk-weighted assets; verify the applicable regulatory threshold.'),
        ('DEMO-KYC-001', 'kyc_status', 'eq', 'complete', 'High', 'Illustrative KYC status must be complete', 'Collect and verify missing KYC documentation.'),
        ('DEMO-EXP-001', 'loan_exposure', 'gte', '0', 'Medium', 'Illustrative loan exposure must be non-negative', 'Reconcile exposure with the source ledger.'),
    ]:
        db.add(RegulatoryRule(organization_id=org, framework_id=framework.id, source_id=source.id, code=code, version='demo-1.0', clause=clause, field=field, operator=operator, threshold=threshold, severity=severity, verified=False, corrective_action=action))
    return framework
