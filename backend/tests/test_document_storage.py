import hashlib
from sqlalchemy import select
from app.config import settings
from app.models import UploadedDocument


def test_database_document_storage_survives_session(client, account, db_factory, monkeypatch):
    monkeypatch.setattr(settings(), 'storage_configuration', 'database')
    content = b'account_id,loan_exposure\nDEMO-A001,100'
    response = client.post('/api/documents/upload', headers=account, files={'file':('synthetic.csv', content)})
    assert response.status_code == 201, response.text
    assert 'source_bytes' not in response.json()
    identifier = response.json()['id']
    with db_factory() as db:
        document = db.scalar(select(UploadedDocument).where(UploadedDocument.id == identifier))
        assert document.storage_path == 'database'
        assert document.source_bytes == content
        assert hashlib.sha256(document.source_bytes).hexdigest() == document.sha256
    listed = client.get('/api/documents', headers=account)
    assert listed.status_code == 200
    assert all('source_bytes' not in row for row in listed.json())
