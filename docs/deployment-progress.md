# Deployment progress — 8 November 2026

- Created private source repository: https://github.com/lachaiahgarivaishnavi18-droid/RegulaTrust-AI
- Pushed the tested source to `codex/regulatrust-deployment` (initial source commit `1abf8c5`).
- Confirmed `.env`, private uploads, local database files, virtual environment, node dependencies and build output are excluded from Git.
- Inspected signed-in GitHub, Vercel and Render accounts. No existing RegulaTrust resource was identified in the inspected project/service lists. Existing unrelated resources were not changed.
- Completed Neon Google sign-in and inspected the Vercel-managed organization.
- Created one isolated Neon database, `regulatrust-db`, on the Free plan in Singapore. Neon project ID: `muddy-moon-75891614`. Vercel storage ID: `store_XMKpQzqeYSPIRRsb`. Auth and Realtime were left disabled.
- Verified TLS connectivity and an empty database, applied migrations 0001 and 0002, and verified all 22 application tables with no schema drift.
- Added PostgreSQL storage of uploaded originals (`STORAGE_CONFIGURATION=database`) for stateless hosts. Binary originals are excluded from API serialization. The updated backend suite passed 33 tests; an additional production-configuration check also passed. Frontend build and four component tests passed after adding a configurable upload limit.
- User authorized the official Vercel CLI via its device sign-in flow. CLI credentials are kept only in the ignored `storage/vercel-cli` directory.
- Created the exact two required Vercel projects: `regulatrust-api` and `regulatrust-ai`, in the existing Hobby team. No prior projects with those names existed.
- Configured the API production environment using stdin for secrets: Neon URL, generated JWT secret, HTTPS frontend origin, PostgreSQL private document storage, and a 4 MB request upload limit suitable for Vercel Functions.
- Prepared clean allowlisted source packages in ignored `storage/deploy/` because Windows denied the CLI access to a test-cache directory. No credentials, uploads, local database files or caches are included.
- API deployment succeeded: https://regulatrust-api.vercel.app/ (deployment `dpl_CnrFLieaVJS2uxXKjGK3RezV17pQ`, READY). The first API build exposed missing dependencies in `pyproject.toml`; runtime dependency declarations were corrected before the successful release.
- Frontend deployment succeeded: https://regulatrust-ai.vercel.app/ (deployment `dpl_B4a8Qi9RDYzdaNZS9rhrJxp8jkbw`, READY).
- The API `/ready` endpoint, live synthetic end-to-end smoke checks and browser login/dashboard all passed. Results are in `cloud-verification.json` and `verification.md`. The synthetic QA browser session was signed out before handoff.
- No paid resources or upgrades were requested or purchased. Existing unrelated projects were not changed.

## Maintenance

Use the existing database and two Vercel projects; do not create replacement resources for routine releases. Secrets are in Vercel production environment settings and ignored local configuration only. Do not paste connection secrets in chat or commit them to Git.

From `backend/`, run `../.venv/Scripts/python.exe ../scripts/neon_setup.py` for read-only connectivity/schema inspection. The helper's live inspection and `--apply` path were verified successfully. It rejects non-Neon hosts, missing TLS and unrelated tables. Use a new reviewed Alembic revision for future schema changes.

Production uses `STORAGE_CONFIGURATION=database` and a 4 MB upload cap. The retained Render blueprint is an undeployed alternative that can require a paid disk. Both existing Vercel projects are now connected to the private GitHub repository. Production branch `main`, repository identity and source roots were verified through authenticated Vercel metadata: API `backend` / FastAPI; frontend `frontend` / Vite. Pushes to `main` trigger the relevant automatic production builds. Configure SMTP and optional LLM providers separately if those features are needed.
