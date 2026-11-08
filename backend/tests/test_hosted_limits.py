from pydantic import ValidationError
import pytest
from app.config import Settings


def test_production_rejects_insecure_database_and_origin():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment='production', jwt_secret='test-secret-at-least-32-characters', database_url='sqlite:///production.db', frontend_url='https://example.com')
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment='production', jwt_secret='test-secret-at-least-32-characters', database_url='postgresql://user:pass@host/db?sslmode=require', frontend_url='http://example.com')
