import base64
import hashlib
import hmac
import secrets
from datetime import UTC

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Membership, SessionToken, User, get_db, now

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return (
        "pbkdf2$600000$"
        + base64.urlsafe_b64encode(salt).decode()
        + "$"
        + base64.urlsafe_b64encode(digest).decode()
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, rounds, salt_text, digest_text = encoded.split("$")
        salt = base64.urlsafe_b64decode(salt_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(digest_text))
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid_session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized
    session = db.get(SessionToken, token_hash(credentials.credentials))
    if not session or session.revoked_at:
        raise unauthorized
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now():
        raise unauthorized
    user = db.get(User, session.user_id)
    if not user:
        raise unauthorized
    request.state.session_hash = session.token_hash
    return user


def membership(db: Session, user_id: str, tenant_id: str) -> Membership:
    item = db.scalar(
        select(Membership).where(Membership.user_id == user_id, Membership.tenant_id == tenant_id)
    )
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item


def require_role(db: Session, user: User, tenant_id: str, *roles: str) -> Membership:
    item = membership(db, user.id, tenant_id)
    if item.role not in roles:
        raise HTTPException(status_code=403, detail="forbidden")
    return item
