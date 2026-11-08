# RegulaTrust API deployment

This directory is the root of the existing Vercel project `regulatrust-api`.

- Git repository: `lachaiahgarivaishnavi18-droid/RegulaTrust-AI`.
- Production branch: `main`.
- Framework: FastAPI, Python 3.12, entrypoint `app.main:app`.
- Production readiness endpoint: https://regulatrust-api.vercel.app/ready
- Build configuration: `vercel.json`; migrations run with `python -m alembic upgrade head`.

Push reviewed backend changes to `main` to trigger production deployment. Keep new schema changes in additive, reviewed Alembic revisions. The production database is the existing Neon `regulatrust-db`; private document originals are stored in PostgreSQL. Secrets remain in Vercel environment settings and ignored local configuration.

The React application is a separate Vercel project rooted at `frontend/`. See the repository's `docs/deployment.md` for verification and operational limits. Never set `TEST_DATABASE_URL` to the live Neon database: the test fixture drops application tables in its dedicated test database.
