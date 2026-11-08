import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Boolean, Float, Integer, LargeBinary, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid():
    return str(uuid.uuid4())


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Tenant:
    organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)


class Organization(Identity, Base):
    __tablename__ = 'organizations'
    name: Mapped[str] = mapped_column(String(160))
    jurisdiction: Mapped[str] = mapped_column(String(80), default='Unconfigured')


class User(Identity, Tenant, Base):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    token_version: Mapped[int] = mapped_column(Integer, default=0)


class Role(Identity, Base):
    __tablename__ = 'roles'
    name: Mapped[str] = mapped_column(String(40), unique=True)


class UserRole(Base):
    __tablename__ = 'user_roles'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    role_id: Mapped[str] = mapped_column(ForeignKey('roles.id'), primary_key=True)


class UploadedDocument(Identity, Tenant, Base):
    __tablename__ = 'uploaded_documents'
    filename: Mapped[str] = mapped_column(String(240))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_path: Mapped[str] = mapped_column(Text)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(40), default='Pending')
    demo: Mapped[bool] = mapped_column(Boolean, default=False)
    mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    source_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)


class RegulatoryFramework(Identity, Tenant, Base):
    __tablename__ = 'regulatory_frameworks'
    name: Mapped[str] = mapped_column(String(100))
    jurisdiction: Mapped[str] = mapped_column(String(80))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class RegulatoryDocument(Identity, Tenant, Base):
    __tablename__ = 'regulatory_documents'
    framework_id: Mapped[str] = mapped_column(ForeignKey('regulatory_frameworks.id'))
    title: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    embedding: Mapped[list] = mapped_column(JSON, default=list)


class RegulatoryRule(Identity, Tenant, Base):
    __tablename__ = 'regulatory_rules'
    framework_id: Mapped[str] = mapped_column(ForeignKey('regulatory_frameworks.id'))
    source_id: Mapped[str | None] = mapped_column(ForeignKey('regulatory_documents.id'))
    code: Mapped[str] = mapped_column(String(80))
    version: Mapped[str] = mapped_column(String(40))
    clause: Mapped[str] = mapped_column(Text)
    field: Mapped[str] = mapped_column(String(80))
    operator: Mapped[str] = mapped_column(String(20))
    threshold: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    corrective_action: Mapped[str] = mapped_column(Text)


class ReportingPeriod(Identity, Tenant, Base):
    __tablename__ = 'reporting_periods'
    label: Mapped[str] = mapped_column(String(80))


class BankingRecord(Identity, Tenant, Base):
    __tablename__ = 'banking_records'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'), index=True)
    period_id: Mapped[str | None] = mapped_column(ForeignKey('reporting_periods.id'))
    row_number: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(JSON)


class DataQualityResult(Identity, Tenant, Base):
    __tablename__ = 'data_quality_results'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'), index=True)
    score: Mapped[float] = mapped_column(Float)
    issues: Mapped[list] = mapped_column(JSON)


class AgentExecution(Identity, Tenant, Base):
    __tablename__ = 'agent_executions'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'), index=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    agent: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[float] = mapped_column(Float, default=0)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[str] = mapped_column(String(80), default='1.0.0')
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class ComplianceValidation(Identity, Tenant, Base):
    __tablename__ = 'compliance_validations'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'), index=True)
    record_id: Mapped[str] = mapped_column(ForeignKey('banking_records.id'))
    rule_id: Mapped[str] = mapped_column(ForeignKey('regulatory_rules.id'))
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(20))
    evidence: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)


class Anomaly(Identity, Tenant, Base):
    __tablename__ = 'anomalies'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'), index=True)
    record_id: Mapped[str] = mapped_column(ForeignKey('banking_records.id'))
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    score: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(20))
    explanation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON)


class RiskAssessment(Identity, Tenant, Base):
    __tablename__ = 'risk_assessments'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'), index=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    score: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(20))
    components: Mapped[dict] = mapped_column(JSON)
    recommendations: Mapped[list] = mapped_column(JSON)


class RegulatoryReport(Identity, Tenant, Base):
    __tablename__ = 'regulatory_reports'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'), index=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default='Requires Review')
    version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot: Mapped[dict] = mapped_column(JSON)


class AuditLog(Identity, Tenant, Base):
    __tablename__ = 'audit_logs'
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(100), index=True)
    details: Mapped[dict] = mapped_column(JSON)


class ReviewerApproval(Identity, Tenant, Base):
    __tablename__ = 'reviewer_approvals'
    report_id: Mapped[str] = mapped_column(ForeignKey('regulatory_reports.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    decision: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str] = mapped_column(Text)
    report_version: Mapped[int] = mapped_column(Integer)


class Notification(Identity, Tenant, Base):
    __tablename__ = 'notifications'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class DocumentEvidence(Identity, Tenant, Base):
    __tablename__ = 'document_evidence'
    document_id: Mapped[str] = mapped_column(ForeignKey('uploaded_documents.id'))
    validation_id: Mapped[str] = mapped_column(ForeignKey('compliance_validations.id'))
    sha256: Mapped[str] = mapped_column(String(64))
    locator: Mapped[str] = mapped_column(Text)


class AuthSession(Identity, Tenant, Base):
    __tablename__ = 'auth_sessions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class PasswordReset(Identity, Base):
    __tablename__ = 'password_resets'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
