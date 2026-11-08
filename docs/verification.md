# Verification record — 8 November 2026

## Passed locally

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
| Supported uploads | CSV API and parser checks; XLSX/PDF parser checks; UI file form implemented |
| Data quality | Passed missing/type/date/duplicate checks |
| Eight-agent orchestration | Passed success, failure and retry checks |
| Evidence-backed deterministic validation | Passed source/version/row/hash checks |
| Anomaly detection | Passed reproducibility, outlier and prior-period checks |
| Explainable risk assessment | Passed persisted assessment checks; formula documented |
| PDF/Excel export | Passed all report kind export checks |
| Human approval | Passed independent approval, rejection, self-review denial and unresolved evidence gates |
| Persistent audit records | Passed database and API checks |
| Neon persistence | **Pending Neon connection and live migration verification** |
| Frontend/backend/database workflow | Passed locally on PostgreSQL |
| Security/integration tests | Passed included tests; independent penetration/security review remains external |
| Working deployment | **Pending Neon access and hosting setup; no cloud deployment claimed** |

## Material limits and remaining verification

The Neon integration was found and suggested after the user selected Neon. It was not installed/connected at the time this record was written. No Neon database URL, Vercel project or Render service was available. No cloud database migration, hosted frontend/backend workflow, SMTP delivery, real LLM provider call, load test, backup restoration or institution-specific regulatory validation has been verified.

The frontend build reports a large JavaScript bundle warning (~712 kB minified, ~205 kB gzip). The backend test environment emits a Starlette warning about future migration from its httpx TestClient adapter. Neither prevented successful tests/builds. Current dependencies are locked; upgrade with verification before a production release.

The initial migration check was first attempted while tests used the same disposable database, causing a duplicate-table error. The tests passed, and the migration was rerun successfully after tests completed. Application development data was unaffected.

See `architecture.md` for synchronous orchestration, local lexical-vector retrieval, statistical model limits, per-process rate limiting, administrator source attestation, storage constraints and operational requirements. Passing the included tests does not establish production banking certification.
