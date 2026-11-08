import re
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime
from pydantic import ConfigDict


class EntityResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str
    organization_id: str
    created_at: datetime


class UserResponse(EntityResponse):
    email: str
    name: str
    roles: list[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal['bearer']
    expires_in: int
    user: UserResponse


class DocumentResponse(EntityResponse):
    filename: str
    sha256: str
    status: str
    demo: bool
    uploaded_by: str
    mapping: dict
    record_count: int | None = None
    preview: list[dict] | None = None


class ValidationResponse(EntityResponse):
    document_id: str
    record_id: str
    rule_id: str
    run_id: str
    status: Literal['Compliant', 'Non-Compliant', 'Needs Review', 'Not Applicable']
    severity: Literal['Critical', 'High', 'Medium', 'Low']
    evidence: dict
    explanation: str
    recommendation: str


class RunResponse(BaseModel):
    run_id: str
    report_id: str
    status: str


class ReportResponse(EntityResponse):
    document_id: str
    run_id: str
    kind: str
    status: str
    version: int


class DashboardResponse(BaseModel):
    reports_processed: int
    report_versions: int
    compliance_score: float | None
    violations: int
    failed_checks: int
    critical_findings: int
    pending_reviews: int
    data_quality_score: float | None
    needs_verification: int
    recent_activity: list[dict]


class Register(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    organization: str = Field(min_length=1, max_length=160)

    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Enter a valid email address')
        return value.lower()


class Login(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class EmailRequest(BaseModel):
    email: str = Field(max_length=254)


class Reset(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=12, max_length=128)


class RunRequest(BaseModel):
    document_id: str


class ReportRequest(RunRequest):
    kind: Literal['Regulatory compliance report', 'Data quality report', 'Anomaly report', 'Risk assessment report', 'Exception report', 'Executive summary'] = 'Regulatory compliance report'


class Decision(BaseModel):
    comment: str = Field(min_length=5, max_length=2000)
    version: int = Field(ge=1)


class RoleRequest(BaseModel):
    role: Literal['Administrator', 'Compliance Officer', 'Banking Analyst', 'Auditor']


class Invite(Register):
    role: Literal['Compliance Officer', 'Banking Analyst', 'Auditor'] = 'Banking Analyst'


class FrameworkRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    jurisdiction: str = Field(min_length=2, max_length=80)
    enabled: bool = False


class SourceRequest(BaseModel):
    framework_id: str
    title: str = Field(min_length=3, max_length=500)
    source_url: str = Field(max_length=2000)
    version: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=10, max_length=100000)
    verified: bool = False

    @field_validator('source_url')
    @classmethod
    def https(cls, value):
        if not value.startswith('https://'):
            raise ValueError('An HTTPS source URL is required')
        return value


class RuleRequest(BaseModel):
    framework_id: str
    source_id: str
    code: str = Field(min_length=2, max_length=80)
    version: str = Field(min_length=1, max_length=40)
    clause: str = Field(min_length=3, max_length=5000)
    field: Literal['capital_ratio', 'capital', 'risk_weighted_assets', 'loan_exposure', 'kyc_status', 'customer_id', 'account_id', 'reporting_date']
    operator: Literal['gte', 'lte', 'eq', 'required']
    threshold: str = Field(max_length=100)
    severity: Literal['Critical', 'High', 'Medium', 'Low']
    verified: bool = False
    corrective_action: str = Field(min_length=3, max_length=2000)


class ProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class OrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    jurisdiction: str = Field(min_length=2, max_length=80)
