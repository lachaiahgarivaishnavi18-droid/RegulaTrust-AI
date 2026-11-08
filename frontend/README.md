# RegulaTrust frontend deployment

This directory is the root of the existing Vercel project `regulatrust-ai`.

- Git repository: `lachaiahgarivaishnavi18-droid/RegulaTrust-AI`.
- Production branch: `main`.
- Framework: Vite / React / TypeScript.
- Production URL: https://regulatrust-ai.vercel.app/
- Build command: `pnpm build`; output directory: `dist`.

Push reviewed frontend changes to `main` to trigger production deployment. Production configuration uses `VITE_API_URL=https://regulatrust-api.vercel.app` and `VITE_MAX_UPLOAD_MB=4`. Only public frontend configuration belongs in `VITE_` variables; database URLs, signing secrets and provider keys remain in the API project's server-side environment.

The API is a separate Vercel project rooted at `backend/`. See the repository's `docs/deployment.md` for verification and operational limits.
