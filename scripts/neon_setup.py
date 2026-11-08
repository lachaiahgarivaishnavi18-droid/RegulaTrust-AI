"""Inspect or migrate the configured Neon database without displaying credentials.

Run from backend/: ../.venv/Scripts/python.exe ../scripts/neon_setup.py [--apply]
"""
import argparse
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs

backend = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(backend))
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from app.config import settings
from app.models import Base


def main():
    parser = argparse.ArgumentParser(description='Inspect the configured Neon database; --apply runs pending Alembic migrations.')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    os.chdir(backend)
    config = settings()
    raw = config.database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    if raw.startswith('postgresql://'):
        raw = raw.replace('postgresql://', 'postgresql+psycopg://', 1)
    url = make_url(raw)
    if not url.host or not url.host.endswith('.neon.tech'):
        raise ValueError('DATABASE_URL must target your selected Neon project; the local development database will not be migrated by this command.')
    if url.query.get('sslmode') not in ('require', 'verify-full'):
        raise ValueError('Neon DATABASE_URL must require TLS using sslmode=require or verify-full.')
    engine = create_engine(url, pool_pre_ping=True, connect_args={'connect_timeout': 15})
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
            existing = set(inspect(connection).get_table_names())
            expected = set(Base.metadata.tables)
            print(f'Neon connection verified over required TLS. Existing public tables: {len(existing)}.')
            if args.apply:
                unknown = existing - expected - {'alembic_version'}
                if unknown:
                    raise ValueError('Database contains unrelated tables. Select an isolated RegulaTrust database before applying migrations.')
                if existing.intersection(expected) and 'alembic_version' not in existing:
                    raise ValueError('Application tables exist without migration history. Operator review is required; no migration was applied.')
        if args.apply:
            from alembic import command
            from alembic.config import Config
            command.upgrade(Config(str(backend / 'alembic.ini')), 'head')
            command.check(Config(str(backend / 'alembic.ini')))
            with engine.connect() as connection:
                found = set(inspect(connection).get_table_names())
                if not expected.issubset(found):
                    raise ValueError('Expected application tables are missing after migration.')
            print(f'Neon schema verified: {len(expected)} application tables. No credentials or banking data printed.')
        else:
            print('Read-only inspection complete. Rerun with --apply to apply the reviewed migration.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    try:
        main()
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        # Database driver errors can contain connection details; never print them.
        print(f'Neon setup failed ({type(error).__name__}). Check secure connection configuration and project access.', file=sys.stderr)
        sys.exit(1)
