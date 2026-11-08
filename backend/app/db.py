from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings


@lru_cache
def engine():
    url = settings().database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return create_engine(url, pool_pre_ping=True)


def session_factory():
    return sessionmaker(engine(), expire_on_commit=False)


def get_db():
    with session_factory()() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise
