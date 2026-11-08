"""Generate ignored local configuration. Never overwrites existing configuration."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
backend = root / 'backend' / '.env'
if not backend.exists():
    backend.write_text('DATABASE_URL=postgresql+psycopg://regulatrust:local-development-only@127.0.0.1:55432/regulatrust\nJWT_SECRET=' + secrets.token_urlsafe(48) + '\nFRONTEND_URL=http://localhost:5173\nENVIRONMENT=development\nSTORAGE_CONFIGURATION=../storage/documents\n', encoding='utf-8')
frontend = root / 'frontend' / '.env'
if not frontend.exists():
    frontend.write_text('VITE_API_URL=http://localhost:8000\n', encoding='utf-8')
print('Local configuration ready. Existing .env files preserved; secrets not printed.')
