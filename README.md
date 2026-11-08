# RegulaTrust AI

An evidence-led banking reporting workspace with eight modular agents, deterministic validation, organization isolation, independent review, persistent PostgreSQL records and PDF/Excel exports.

**Live app:** https://regulatrust-ai.vercel.app/ · **API:** https://regulatrust-api.vercel.app/ready

**Status:** deployed on Vercel with Neon PostgreSQL. Cloud signup, CSV/XLSX/PDF uploads, eight-agent processing, evidence, anomaly/risk analysis, PDF/Excel exports, independent rejection/approval gates, logout revocation, audit persistence and private document originals were verified with synthetic data. Included demonstration controls never certify bank compliance. Create your account in the live app to start your own isolated workspace.

The hosted upload limit is **4 MB** to fit Vercel Functions. Local installations default to 10 MB. SMTP password recovery and optional LLM narratives still require separately configured providers. See `docs/verification.md` for tested scope and remaining operational requirements.

## Repository

- `frontend/` — React, TypeScript, Vite, Tailwind, Radix/shadcn-style components, Recharts, Lucide; nine connected workspace screens.
- `backend/app/` — FastAPI, SQLAlchemy models, RBAC, ingestion, knowledge retrieval, agents, orchestration and exports.
- `backend/alembic/` — schema migration.
- `backend/tests/` — unit, security, API and database workflow tests.
- `tools/` — optional persistent workspace-local PostgreSQL runtime for Windows development.
- `scripts/configure_local.py` — generate ignored `.env` files without overwriting existing files.
- `scripts/neon_setup.py` — guarded Neon inspection and migration verification.
- `scripts/package_deployment.py` — package an explicit source allowlist for deployment.
- `scripts/cloud_smoke.py` — live workflow checks using clearly labeled synthetic data.
- `docs/architecture.md` — trust boundaries, formulas, assumptions and limitations.
- `docs/deployment.md` — Vercel / Render / Neon setup and operational requirements.
- `docs/verification.md` — actual checks run and remaining acceptance gates.

## Run locally (Windows PowerShell)

Requires Python 3.12, Node.js 22+ and pnpm. Use your Python 3.12 executable if `python` points at another version.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
cd frontend
pnpm install
cd ..\tools
pnpm install
node postgres.mjs
```

The optional local PostgreSQL process uses port 55432 and persists to `storage/postgres`. Keep its terminal running. Default development database user is `regulatrust`, password `local-development-only`; it listens on loopback. These defaults must never be used in production. Set `LOCAL_DB_PASSWORD` before creating a new cluster to use a custom password, and update `backend/.env` accordingly. Existing cluster passwords do not change when changing the environment variable.

In another terminal:

```powershell
.\.venv\Scripts\python.exe scripts/configure_local.py
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a third terminal:

```powershell
cd frontend
pnpm dev
```

Open `http://localhost:5173`. Create your own account. Use **Load & validate demo** for explicitly labeled synthetic data. Add an independent compliance officer under Settings to review reports. Illustrative demo reports can be rejected; they cannot be approved as verified compliance.

Alternatively use an existing PostgreSQL database or `compose.yaml` (requires Docker and `POSTGRES_PASSWORD`), then set `DATABASE_URL` appropriately. No SQLite fallback exists in production configuration. Unit/API tests can use isolated temporary SQLite only as a fast test adapter; the same suite is also tested on PostgreSQL.

## Test and build

```powershell
cd backend
New-Item -ItemType Directory -Force .test-tmp | Out-Null
..\.venv\Scripts\python.exe -m pytest -q --basetemp=.test-tmp/local-run
# Use a dedicated, disposable PostgreSQL TEST database for the full dialect run:
$env:TEST_DATABASE_URL='postgresql+psycopg://regulatrust:local-development-only@127.0.0.1:55432/regulatrust_test'
..\.venv\Scripts\python.exe -m pytest -q --basetemp=.test-tmp/postgres-run
..\.venv\Scripts\python.exe -m alembic check
cd ..\frontend
pnpm test
pnpm build
```

**TEST_DATABASE_URL must point to a dedicated disposable database.** The integration fixture creates and drops the application tables in that database. Never point it at development, production, or an existing business database. CI provisions an isolated PostgreSQL service.

## Input schema

```csv
customer_id,account_id,reporting_date,capital,risk_weighted_assets,loan_exposure,kyc_status
DEMO-C0001,DEMO-A0001,2026-09-30,15000,100000,12500,complete
```

Dates use ISO `YYYY-MM-DD`; amounts must be finite and non-negative, and risk-weighted assets positive. Upload supports source-to-standard column mapping, e.g. `{"customer_number":"customer_id"}`. PDF support is limited to text PDFs containing CSV-formatted tables; scanned/ambiguous PDFs are rejected. XLSX cells must contain values, not formulas.

## API

Interactive OpenAPI documentation: `http://localhost:8000/docs`. Auth uses bearer JWT access tokens returned by register/login. Registration creates an isolated organization. See the generated OpenAPI document for request schemas.

Endpoints include auth register/login/logout/me/forgot-password/reset-password, profile, documents/upload/list/detail, agents/run/status/executions, compliance/validate/results/findings, dashboard/summary/compliance/risks, quality, anomalies, risks/summary, reports/generate/list/detail/download/recommendation, approvals/approve/reject, audit-logs, settings, users/roles, frameworks, knowledge sources/search and versioned rules.

Configuration examples are in `backend/.env.example` and `frontend/.env.example`. Backend secrets stay on the backend; only `VITE_API_URL` is public frontend configuration. LLM recommendations and SMTP password recovery require explicitly configured providers. Deterministic agents operate without an LLM key.
