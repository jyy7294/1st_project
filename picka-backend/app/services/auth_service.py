from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException
from app.core.config import settings
from app.models import User


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


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
            "iat": now,
            "exp": now
            + timedelta(minutes=settings.access_token_expire_minutes),
        },
        _jwt_secret(),
        algorithm=settings.jwt_algorithm,
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


def login_response(
    user: User,
) -> dict[str, Any]:
    return {
        "message": "로그인에 성공했습니다.",
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": auth_user_payload(
            user,
        ),
    }
