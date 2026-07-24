from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import AuthRefreshToken, User


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
bearer_scheme = HTTPBearer(auto_error=False)
REVOKED_TOKEN_RETENTION_DAYS = 7


def delete_stale_refresh_tokens(
    db: Session,
    *,
    now: datetime | None = None,
) -> int:
    checked_at = now or datetime.now(timezone.utc)
    revoked_cutoff = checked_at - timedelta(days=REVOKED_TOKEN_RETENTION_DAYS)
    result = db.execute(
        delete(AuthRefreshToken).where(or_(
            AuthRefreshToken.expires_at <= checked_at,
            AuthRefreshToken.revoked_at <= revoked_cutoff,
        ))
    )
    return int(result.rowcount or 0)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    return "$".join(
        (
            "scrypt",
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            base64.urlsafe_b64encode(salt).decode(),
            base64.urlsafe_b64encode(digest).decode(),
        )
    )


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$", 5)
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode(),
            salt=base64.urlsafe_b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
        )
        return hmac.compare_digest(
            digest,
            base64.urlsafe_b64decode(expected),
        )
    except (ValueError, TypeError):
        return False


def _jwt_secret() -> str:
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=503,
            detail="인증 서비스 설정이 완료되지 않았습니다.",
        )
    return settings.jwt_secret_key


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now
            + timedelta(minutes=settings.access_token_expire_minutes),
        },
        _jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(db: Session, user: User) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    jti = str(uuid4())
    token = jwt.encode(
        {
            "sub": str(user.id),
            "type": "refresh",
            "jti": jti,
            "iat": now,
            "exp": expires_at,
        },
        _jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )
    db.add(AuthRefreshToken(
        user_id=user.id,
        jti=jti,
        token_hash=_token_hash(token),
        expires_at=expires_at,
    ))
    return token


def _decode_refresh_token(token: str) -> tuple[dict[str, Any], int]:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효한 Refresh Token이 필요합니다.",
    )
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "refresh" or not payload.get("jti"):
            raise unauthorized
        return payload, int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
        raise unauthorized from error


def rotate_refresh_token(db: Session, token: str) -> dict[str, Any]:
    payload, user_id = _decode_refresh_token(token)
    row = db.scalar(select(AuthRefreshToken).where(
        AuthRefreshToken.token_hash == _token_hash(token),
        AuthRefreshToken.jti == payload["jti"],
        AuthRefreshToken.user_id == user_id,
    ))
    if row is None or row.revoked_at is not None:
        if row is not None:
            db.execute(
                update(AuthRefreshToken)
                .where(
                    AuthRefreshToken.user_id == user_id,
                    AuthRefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(timezone.utc))
            )
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="폐기되었거나 이미 사용된 Refresh Token입니다.",
        )
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효한 Refresh Token이 필요합니다.",
        )
    row.revoked_at = datetime.now(timezone.utc)
    new_refresh_token = create_refresh_token(db, user)
    db.commit()
    return token_pair_payload(user, new_refresh_token)


def revoke_refresh_token(db: Session, token: str) -> None:
    payload, user_id = _decode_refresh_token(token)
    row = db.scalar(select(AuthRefreshToken).where(
        AuthRefreshToken.token_hash == _token_hash(token),
        AuthRefreshToken.jti == payload["jti"],
        AuthRefreshToken.user_id == user_id,
    ))
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.commit()


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효한 인증 토큰이 필요합니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials,
            _jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise unauthorized
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
        raise unauthorized from error
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_user_access(requested_user_id: int, current_user: User) -> None:
    if requested_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 정보에 접근할 수 없습니다.",
        )


def require_admin(current_user: User) -> None:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )


def auth_user_payload(
    user: User,
) -> dict[str, Any]:
    return {
        "user_id": user.id,
        "username": None,
        "email": user.email,
        "name": user.name,
    }


def token_pair_payload(user: User, refresh_token: str) -> dict[str, Any]:
    return {
        "access_token": create_access_token(user),
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": auth_user_payload(user),
    }


def login_response(db: Session, user: User) -> dict[str, Any]:
    refresh_token = create_refresh_token(db, user)
    db.commit()
    return {
        "message": "로그인에 성공했습니다.",
        **token_pair_payload(user, refresh_token),
    }
