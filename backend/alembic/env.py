from alembic import context
from app.db import engine
from app.models import Base

target_metadata = Base.metadata
if context.is_offline_mode():
    from app.config import settings
    context.configure(url=settings().database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
