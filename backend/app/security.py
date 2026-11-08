from datetime import timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User, Role, UserRole, AuthSession, AuditLog, now

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
ROLES = ['Administrator', 'Compliance Officer', 'Banking Analyst', 'Auditor']


def roles(db, user):
    return list(db.scalars(select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)))


def audit(db, user, action, details):
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action=action, details=details))


def issue_token(db, user):
    expires = now() + timedelta(minutes=30)
    session = AuthSession(organization_id=user.organization_id, user_id=user.id, expires_at=expires)
    db.add(session)
    db.flush()
    token = jwt.encode({'sub': user.id, 'sid': session.id, 'ver': user.token_version, 'exp': expires, 'iat': now(), 'iss': 'regulatrust', 'aud': 'regulatrust-api'}, settings().jwt_secret, algorithm='HS256')
    return {'access_token': token, 'token_type': 'bearer', 'expires_in': 1800}


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    try:
        if not credentials:
            raise ValueError()
        payload = jwt.decode(credentials.credentials, settings().jwt_secret, algorithms=['HS256'], issuer='regulatrust', audience='regulatrust-api')
        user = db.get(User, payload['sub'])
        session = db.get(AuthSession, payload['sid'])
        if not user or not session or session.revoked or session.user_id != user.id or session.expires_at.replace(tzinfo=timezone.utc) < now() or payload['ver'] != user.token_version:
            raise ValueError()
        return user
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})


def require(*allowed):
    def dependency(user: User = Depends(current_user), db: Session = Depends(get_db)):
        if not set(roles(db, user)).intersection(allowed):
            raise HTTPException(403, 'Your role cannot perform this action')
        return user
    return dependency
