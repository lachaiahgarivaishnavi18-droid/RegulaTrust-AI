"""Maintainer helper: generate the first migration before the first release only."""
from pathlib import Path
from sqlalchemy import create_engine
from alembic.migration import MigrationContext
from alembic.autogenerate import produce_migrations, render_python_code
from app.models import Base

with create_engine('sqlite://').connect() as connection:
    migration = produce_migrations(MigrationContext.configure(connection), Base.metadata)
    upgrade = render_python_code(migration.upgrade_ops)
    downgrade = render_python_code(migration.downgrade_ops)
header = '''"""Initial normalized application schema (frozen at revision 0001)."""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

'''
target = Path('alembic/versions/0001_initial.py')
target.write_text(header + 'def upgrade():\n' + upgrade + '\n\ndef downgrade():\n' + downgrade + '\n', encoding='utf-8')
print('Frozen initial migration. Use a new revision for all subsequent schema changes.')
