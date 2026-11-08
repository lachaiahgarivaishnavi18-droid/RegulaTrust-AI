# Verification record — 8 November 2026

## Verified live deployment

- Frontend: https://regulatrust-ai.vercel.app/
- FastAPI readiness: https://regulatrust-api.vercel.app/ready (HTTP 200, database ready).
- Neon Free database `regulatrust-db`, Singapore; migrations 0001/0002 applied, 22 application tables verified with no schema drift.
- `scripts/cloud_smoke.py` passed registration/login, production CORS, database-backed dashboard, eight completed agents, 96 evidence-backed demo validations, anomaly/risk persistence, CSV/XLSX/PDF uploads, PDF/XLSX exports, self-approval denial, independent reviewer rejection, unverified report approval denial, audit persistence, logout revocation and data persistence across fresh sessions.
- A direct Neon ORM check confirmed the uploaded CSV original persists in the private binary column and matches its hash. The binary was not exposed in API responses.
- The deployed frontend was opened in the browser and signed into the synthetic verification workspace. Its dashboard loaded from the live API/Neon database, with no captured console errors. The QA session was signed out before handoff. Screenshot: `docs/screenshots/deployed-dashboard-desktop.jpg`.
- Machine-readable cloud results: `docs/cloud-verification.json`. All cloud test data is explicitly synthetic.
- The hosted file upload limit is 4 MB. SMTP recovery delivery and real LLM provider calls remain unconfigured and unverified; the API returns explicit unavailable responses for those optional connections.

## Passed locally

- **Final updated backend suite: 34 tests passed** using the isolated local test adapter after the hosting/storage changes. The live Neon smoke workflow separately verifies the deployed PostgreSQL path and original-byte persistence.

- **32 backend tests passed** against persistent local PostgreSQL 18.6 using psycopg/SQLAlchemy.
- **4 frontend component tests passed** using Vitest and Testing Library.
- `pnpm install --offline --frozen-lockfile` succeeded with explicit esbuild build-script approval.
- TypeScript compilation and Vite production build succeeded.
- The frozen Alembic initial migration succeeded in the dedicated test database; `alembic check` reported no new upgrade operations.
- `/ready` returned `{"status":"ready"}` against the development PostgreSQL schema.
- Frontend HTTP endpoint returned 200.
- Browser registration created a synthetic sandbox account and loaded the database-backed dashboard.
- Browser **Run synthetic demo** created 32 explicitly synthetic records, executed all eight agents, persisted 96 review-required validations, generated a report and showed evidence and independent review controls.
- Browser checks at desktop width 1440 and mobile width 390 found no document-level horizontal overflow. Mobile navigation opened and selected the compliance view. Wide tables scroll within their own container.
- No browser console errors were captured during this workflow.
- Browser screenshots are saved in `docs/screenshots/`.

The backend suite verifies deterministic capital controls (including invalid denominators and non-finite inputs), demo non-certification, CSV/XLSX/text-table PDF parsing, formula rejection, masking, unsupported/oversized uploads, quality checks, reproducible statistical and historical anomaly detection, vector retrieval, all-eight-agent execution, retry/failure history, tenant isolation, audit persistence, role restrictions, independent approval/rejection and duplicate-review protection, all six report kinds and PDF/XLSX outputs, JWT tampering/expiry/audience/issuer/version checks, logout revocation, one-use password reset/session revocation, role-change session invalidation, SQL injection attempts, cross-tenant source creation, CORS allowlisting and authentication rate limits.

Synthetic administrator-verified sources in tests are test fixtures only; they are not legal authority. Demo controls remain unverified.

## Acceptance criteria

| Requested criterion | Verified status |
| --- | --- |
| Account creation and login | Passed API and browser checks |
| Role-based access | Passed administrator, officer, analyst and auditor checks |
| Database-backed dashboard | Passed API and browser workflow |
| Supported uploads | CSV, XLSX and structured PDF uploads passed on the live API; parser and rejection checks passed locally |
| Data quality | Passed missing/type/date/duplicate checks |
| Eight-agent orchestration | Passed success, failure and retry checks |
| Evidence-backed deterministic validation | Passed source/version/row/hash checks |
| Anomaly detection | Passed reproducibility, outlier and prior-period checks |
| Explainable risk assessment | Passed persisted assessment checks; formula documented |
| PDF/Excel export | Passed all report kind export checks |
| Human approval | Passed independent approval, rejection, self-review denial and unresolved evidence gates |
| Persistent audit records | Passed database and API checks |
| Neon persistence | Passed live migrations, ORM schema check, records/audit persistence and private original-byte verification |
| Frontend/backend/database workflow | Passed live cloud API checks and deployed browser sign-in/dashboard |
| Security/integration tests | Passed included tests; independent penetration/security review remains external |
| Working deployment | Passed: both Vercel deployments are READY and production URLs respond successfully |

## Material limits and remaining verification

Neon was provisioned through the existing Vercel-managed organization. The production environment uses Neon and the official Vercel CLI, authorized by the user. SMTP delivery, real LLM provider calls, load testing, backup restoration and institution-specific regulatory validation remain unverified. Render was not deployed; both API and frontend run on Vercel. No paid upgrade was performed.

The frontend build reports a large JavaScript bundle warning (~712 kB minified, ~205 kB gzip). The backend test environment emits a Starlette warning about future migration from its httpx TestClient adapter. Neither prevented successful tests/builds. Current dependencies are locked; upgrade with verification before a production release.

The initial migration check was first attempted while tests used the same disposable database, causing a duplicate-table error. The tests passed, and the migration was rerun successfully after tests completed. Application development data was unaffected.

See `architecture.md` for synchronous orchestration, local lexical-vector retrieval, statistical model limits, per-process rate limiting, administrator source attestation, storage constraints and operational requirements. Passing the included tests does not establish production banking certification.
