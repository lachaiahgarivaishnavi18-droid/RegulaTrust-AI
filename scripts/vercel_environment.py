"""Configure only RegulaTrust's deployment variables; secrets travel over stdin."""
import argparse
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
node = shutil.which('node')
pnpm = Path(node).parent.parent / 'node_modules' / 'pnpm' / 'bin' / 'pnpm.mjs'
if not pnpm.exists():
    raise SystemExit('Cannot locate the configured pnpm runtime.')
base = [node, str(pnpm), 'dlx', 'vercel@latest']
config = str(root / 'storage' / 'vercel-cli')


def run(arguments, value=None):
    result = subprocess.run(base + arguments + ['--scope','resume-project3','--global-config',config], cwd=root, input=value, text=True, capture_output=True, env={**os.environ,'VERCEL_TELEMETRY_DISABLED':'1'})
    if result.returncode:
        # Never emit CLI output for a failed secret write.
        raise RuntimeError('Vercel configuration command failed; no credentials printed: ' + arguments[0])
    print('Configured ' + arguments[2] if arguments[:2] == ['env','add'] else 'Vercel project linked.')


def configure():
    parser=argparse.ArgumentParser()
    parser.add_argument('target', choices=['api','frontend'])
    parser.add_argument('--api-url', default='https://regulatrust-api.vercel.app')
    parser.add_argument('--frontend-url', default='https://regulatrust-ai.vercel.app')
    args=parser.parse_args()
    if not args.api_url.startswith('https://') or not args.frontend_url.startswith('https://'):
        raise ValueError('Hosting origins must use HTTPS')
    project='regulatrust-api' if args.target=='api' else 'regulatrust-ai'
    if args.target=='api':
        values=dotenv_values(root/'backend'/'.env')
        url=values.get('DATABASE_URL','')
        if '.neon.tech' not in url:
            raise ValueError('The selected backend configuration must use Neon')
        secrets_file=root/'storage'/'config'/'production-secrets.env'
        if secrets_file.exists():
            jwt_secret=dotenv_values(secrets_file)['JWT_SECRET']
        else:
            jwt_secret=secrets.token_urlsafe(48)
            secrets_file.parent.mkdir(parents=True,exist_ok=True)
            secrets_file.write_text('JWT_SECRET='+jwt_secret+'\n',encoding='utf-8')
        configuration={'DATABASE_URL':url,'JWT_SECRET':jwt_secret,'ENVIRONMENT':'production','FRONTEND_URL':args.frontend_url.rstrip('/'),'STORAGE_CONFIGURATION':'database','MAX_UPLOAD_BYTES':str(4*1024*1024)}
        secret_keys={'DATABASE_URL','JWT_SECRET'}
    else:
        configuration={'VITE_API_URL':args.api_url.rstrip('/'),'VITE_MAX_UPLOAD_MB':'4'}
        secret_keys=set()
    for name,value in configuration.items():
        run(['env','add',name,'--environment','production','--project',project,'--yes','--force', '--sensitive' if name in secret_keys else '--no-sensitive'],str(value))
    print('Deployment environment configured. Secret values were not logged or passed in command arguments.')


if __name__=='__main__':
    configure()
