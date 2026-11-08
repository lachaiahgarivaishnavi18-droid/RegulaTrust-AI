"""Optional private document persistence in PostgreSQL for stateless hosts."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('uploaded_documents', sa.Column('source_bytes', sa.LargeBinary(), nullable=True))


def downgrade():
    op.drop_column('uploaded_documents', 'source_bytes')
