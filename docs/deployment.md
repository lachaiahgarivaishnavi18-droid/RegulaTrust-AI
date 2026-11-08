# Deployment: Vercel + Neon (Render alternative retained)

The frontend is deployed at https://regulatrust-ai.vercel.app/ and the FastAPI backend at https://regulatrust-api.vercel.app/. Both use the existing Vercel Hobby team. Neon `regulatrust-db` is on the Free plan in Singapore. `/ready` returned 200 with a ready database, and the synthetic cloud smoke workflow passed. No paid upgrade was performed. The retained Render blueprint is an alternative and was not deployed.

## Current Vercel API deployment

The API uses `backend/vercel.json`, Python 3.12, and the FastAPI entrypoint `app.main:app`. Vercel installs the explicitly pinned runtime dependencies in `backend/pyproject.toml`, then runs the Alembic build command. Both schema migrations have been applied to Neon; all 22 application tables and no schema drift were verified.

`STORAGE_CONFIGURATION=database` stores uploaded originals in an organization-scoped PostgreSQL bytea column. Originals are deferred in ORM queries and excluded from API serialization. This supports stateless hosts without a paid persistent disk. Backend secrets were configured through stdin and are not in source control or frontend assets. The production origins are explicitly allowlisted with HTTPS.

The API has `MAX_UPLOAD_BYTES=4194304`, and the frontend has `VITE_MAX_UPLOAD_MB=4`. This leaves room for multipart overhead under Vercel Functions' 4.5 MB request limit. Local installations can retain the 10 MB default. Large-scale processing remains subject to function duration/response limits and the synchronous orchestration limits documented in `architecture.md`.

The initial releases were deployed using the authorized Vercel CLI from clean allowlisted packages in ignored `storage/deploy/`. Both existing projects are now connected to `lachaiahgarivaishnavi18-droid/RegulaTrust-AI`, with `main` as the production branch. `regulatrust-api` uses root directory `backend` and the FastAPI framework; `regulatrust-ai` uses root directory `frontend` and Vite. Pushes to `main` automatically trigger the relevant production builds. Vercel can skip an unaffected project in this monorepo. Production environment variables and the existing Neon database remain configured on the same projects.

## Database

Create or select a Neon PostgreSQL database. Set backend `DATABASE_URL` to the provider's connection URL with `sslmode=require` (or `verify-full` with appropriate certificate configuration). SQLAlchemy uses psycopg v3. The application accepts `postgres://`, `postgresql://`, and `postgresql+psycopg://` URLs; normalized URLs are only held server-side. Use a least-privilege application role and a separate migration role in production. Do not share database URLs in chat, logs, frontend code, or source control.

Run `alembic upgrade head` from `backend/` against the intended database. Back up existing databases before migration. The migration is additive for a new installation. `alembic check` should report no new operations. `/ready` verifies database connectivity and migrated schema; `/health` only verifies the process.

## Backend on Render

`render.yaml` describes a Python 3.12 backend with migrations, health checks and a persistent private document disk. A persistent disk may require a paid Render service; review account pricing before applying the blueprint. No paid service or upgrade is authorized automatically by these files. An ephemeral filesystem is not suitable for uploaded banking documents. Use a durable private volume or extend the storage adapter to an institution-approved private object store before a production launch.

Required server variables:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Neon PostgreSQL connection string with TLS required |
| `JWT_SECRET` | Cryptographically random secret, at least 32 characters |
| `ENVIRONMENT` | `production` |
| `FRONTEND_URL` | Exact HTTPS frontend origin (no trailing slash) |
| `STORAGE_CONFIGURATION` | `database` for Neon-backed originals, or a durable private writable directory |
| `PORT` | Supplied by Render |

Optional narrative provider: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` (OpenAI-compatible chat completions interface). Optional password recovery: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`; STARTTLS is required. Missing providers produce clear unavailable responses. No secret is returned by Settings.

Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Use one worker for the current per-process limiter and synchronous orchestrator; production scale requires a shared rate limiter and supervised job queue. Run migrations as a controlled release step for multi-instance deployments.

## Frontend on Vercel

Select `frontend/` as root, Vite as framework, `pnpm build` as build command, and `dist` as output. Set `VITE_API_URL` to the backend's HTTPS origin. It is a public URL, never a credential. `frontend/vercel.json` handles SPA fallback and basic response headers. Configure a tested Content Security Policy with the backend origin at your hosting layer.

The frontend sends an Authorization bearer token, holds it in memory and requires login after reload. Configure TLS everywhere. Set `FRONTEND_URL` on the backend to the final Vercel origin so the CORS allowlist matches. This build uses explicit API URLs in production; Vite's local proxy is development-only.

## Production acceptance gates

1. Verify Neon connectivity, migrations, backup/restore, encryption and tenant-isolation tests with the deployment role.
2. Register two independent test organizations and confirm cross-organization requests return 404.
3. Add a reviewer and confirm uploader self-approval is denied.
4. Upload synthetic CSV/XLSX/PDF, run all agents, inspect source evidence, export both formats and verify persisted audit history after service restart.
5. Confirm illustrative/unknown requirements cannot yield verified compliance or approved reports.
6. Test SMTP recovery delivery, expiry, one-use tokens and session revocation. Test optional LLM failure and data disclosure policy before enabling it.
7. Configure durable private storage, malware scanning, retention/deletion policy, least-privilege DB permissions, immutable external audit retention, monitoring/alerts, centralized rate limiting and orchestration crash recovery.
8. Have authorized staff verify source documents, institution applicability, rule thresholds, filing periods and report format requirements. Built-in demo controls have no legal authority.
9. Complete institution-specific security review and load/operational testing before handling real banking data.

Do not reuse an existing deployment until its identity and configuration have been inspected. Avoid duplicate resources. No paid upgrades, database deletion, or existing resource deletion are performed by the application setup.
