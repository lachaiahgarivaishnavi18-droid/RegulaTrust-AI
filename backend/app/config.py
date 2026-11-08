from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://localhost/regulatrust'
    jwt_secret: str = ''
    frontend_url: str = 'http://localhost:5173'
    environment: str = 'development'
    storage_configuration: str = './storage'
    llm_api_key: str = ''
    llm_base_url: str = 'https://api.openai.com/v1'
    llm_model: str = ''
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_username: str = ''
    smtp_password: str = ''
    smtp_from: str = ''
    max_upload_bytes: int = 10 * 1024 * 1024

    @model_validator(mode='after')
    def secure(self):
        if len(self.jwt_secret) < 32 or self.jwt_secret.startswith('REPLACE_'):
            raise ValueError('JWT_SECRET must contain at least 32 characters')
        if self.environment == 'production':
            if not self.database_url.startswith(('postgres://', 'postgresql://', 'postgresql+psycopg://')):
                raise ValueError('Production requires PostgreSQL')
            if 'sslmode=verify-full' not in self.database_url and 'sslmode=require' not in self.database_url:
                raise ValueError('Production PostgreSQL must require TLS')
            if not self.frontend_url.startswith('https://'):
                raise ValueError('Production requires HTTPS FRONTEND_URL')
        return self


@lru_cache
def settings():
    return Settings()
