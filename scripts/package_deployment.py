"""Copy an explicit source allowlist into an ignored, clean deployment directory."""
import argparse
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('target',choices=['api','frontend'])
parser.add_argument('label')
args=parser.parse_args()
if not args.label.replace('-','').isalnum():
    raise SystemExit('Use an alphanumeric deployment label.')
source=root/('backend' if args.target=='api' else 'frontend')
destination=root/'storage'/'deploy'/f'{args.target}-{args.label}'
if destination.exists():
    raise SystemExit('Package directory already exists; choose a new label.')
destination.mkdir(parents=True)
paths=['app','alembic','alembic.ini','requirements.txt','requirements.lock.txt','pyproject.toml','vercel.json','.python-version','.vercelignore'] if args.target=='api' else ['src','index.html','package.json','pnpm-lock.yaml','pnpm-workspace.yaml','postcss.config.js','tailwind.config.js','tsconfig.json','vite.config.ts','vercel.json','.vercelignore']
for relative in paths:
    item=source/relative
    if item.is_dir():
        shutil.copytree(item,destination/relative,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    else:
        shutil.copyfile(item,destination/relative)
print(destination)
