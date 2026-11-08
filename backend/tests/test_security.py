import hashlib
from datetime import timedelta
from sqlalchemy import select
import jwt
from app.models import PasswordReset, User, now
from app.config import settings


def test_tampered_expired_and_wrong_audience_tokens(client,account):
    original=account['Authorization'].split(' ',1)[1]
    claims=jwt.decode(original,settings().jwt_secret,algorithms=['HS256'],audience='regulatrust-api',issuer='regulatrust')
    variants=[original+'tampered']
    for updates in [{'exp':now()-timedelta(minutes=1)},{'aud':'wrong-service'},{'iss':'wrong-issuer'},{'ver':999}]:
        variants.append(jwt.encode({**claims,**updates},settings().jwt_secret,algorithm='HS256'))
    for token in variants:
        assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==401


def test_password_reset_revokes_sessions_and_is_single_use(client,account,db_factory):
    token='synthetic-password-reset-token-1234567890'
    with db_factory() as db:
        user=db.scalar(select(User).where(User.email=='admin@example.com'))
        db.add(PasswordReset(user_id=user.id,token_hash=hashlib.sha256(token.encode()).hexdigest(),expires_at=now()+timedelta(minutes=10)))
        db.commit()
    result=client.post('/api/auth/reset-password',json={'token':token,'password':'New-strong-test-password-123'})
    assert result.status_code==200,result.text
    assert client.get('/api/auth/me',headers=account).status_code==401
    assert client.post('/api/auth/reset-password',json={'token':token,'password':'Another-test-password-123'}).status_code==400
    assert client.post('/api/auth/login',json={'email':'admin@example.com','password':'Strong-test-password-123'}).status_code==401
    assert client.post('/api/auth/login',json={'email':'admin@example.com','password':'New-strong-test-password-123'}).status_code==200


def test_missing_smtp_and_llm_are_explicit(client,account):
    assert client.post('/api/auth/forgot-password',json={'email':'admin@example.com'}).status_code==503
    assert client.get('/api/settings',headers=account).json()['llm']['configured'] is False


def test_role_change_invalidates_existing_session(client,account):
    created=client.post('/api/users',headers=account,json={'name':'Analyst','email':'analyst@example.com','password':'Strong-test-password-123','organization':'ignored','role':'Banking Analyst'}).json()
    signed=client.post('/api/auth/login',json={'email':'analyst@example.com','password':'Strong-test-password-123'}).json()
    analyst={'Authorization':'Bearer '+signed['access_token']}
    assert client.post('/api/frameworks',headers=analyst,json={'name':'Wrong','jurisdiction':'Test'}).status_code==403
    assert client.patch('/api/users/'+created['id']+'/role',headers=account,json={'role':'Auditor'}).status_code==200
    assert client.get('/api/auth/me',headers=analyst).status_code==401


def test_sql_injection_does_not_bypass_authentication(client,account):
    result=client.post('/api/auth/login',json={'email':"admin@example.com' OR 1=1 --",'password':'anything'})
    assert result.status_code==401
    assert client.get('/api/documents/not-an-id%27%20OR%201=1',headers=account).status_code==404


def test_framework_and_source_scope(client,account):
    framework=client.post('/api/frameworks',headers=account,json={'name':'Synthetic controls','jurisdiction':'Test only','enabled':True}).json()
    foreign=client.post('/api/auth/register',json={'name':'Other','organization':'Other','email':'other@example.com','password':'Strong-test-password-123'}).json()
    foreign_headers={'Authorization':'Bearer '+foreign['access_token']}
    payload={'framework_id':framework['id'],'title':'Synthetic source','source_url':'https://example.com','version':'1','text':'Synthetic source content for testing','verified':True}
    assert client.post('/api/knowledge/sources',headers=foreign_headers,json=payload).status_code==404
    payload['source_url']='javascript:alert(1)'
    assert client.post('/api/knowledge/sources',headers=account,json=payload).status_code==422


def test_cors_only_trusted_origin(client):
    result=client.options('/api/auth/login',headers={'Origin':settings().frontend_url,'Access-Control-Request-Method':'POST'})
    assert result.headers['access-control-allow-origin']==settings().frontend_url
    bad=client.options('/api/auth/login',headers={'Origin':'https://evil.example','Access-Control-Request-Method':'POST'})
    assert 'access-control-allow-origin' not in bad.headers
