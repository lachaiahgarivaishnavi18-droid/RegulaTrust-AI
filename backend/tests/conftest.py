import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

os.environ['JWT_SECRET'] = 'test-only-secret-not-for-production-012345678901'
os.environ['ENVIRONMENT'] = 'test'
from app.models import Base
from app.main import app, rates
from app.db import get_db
from app.config import settings


@pytest.fixture
def db_factory(tmp_path):
    # SQLite is isolated test storage only. PostgreSQL CI uses the same suite via TEST_DATABASE_URL.
    url = os.environ.get('TEST_DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    yield sessionmaker(engine, expire_on_commit=False)
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_factory, tmp_path, monkeypatch):
    rates.clear()
    monkeypatch.setattr(settings(), 'storage_configuration', str(tmp_path / 'private'))
    def override():
        with db_factory() as db:
            try:
                yield db
            except Exception:
                db.rollback()
                raise
    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def account(client):
    result = client.post('/api/auth/register', json={'name':'Test Admin','email':'admin@example.com','password':'Strong-test-password-123','organization':'Synthetic Bank'})
    assert result.status_code == 201, result.text
    payload = result.json()
    return {'Authorization':'Bearer '+payload['access_token']}
