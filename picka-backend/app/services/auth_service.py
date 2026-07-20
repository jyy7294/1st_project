from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import SocialAccount, User


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


def create_access_token(user: User, login_provider: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "login_provider": login_provider,
            "iat": now,
            "exp": now
            + timedelta(minutes=settings.access_token_expire_minutes),
        },
        _jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )


def create_oauth_state(provider: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "type": "oauth_state",
            "provider": provider,
            "nonce": base64.urlsafe_b64encode(os.urandom(18)).decode(),
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        _jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )


def verify_oauth_state(state: str, provider: str) -> None:
    try:
        payload = jwt.decode(
            state,
            _jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=400,
            detail="소셜 로그인 인증에 실패했습니다.",
        ) from error
    if (
        payload.get("type") != "oauth_state"
        or payload.get("provider") != provider
    ):
        raise HTTPException(
            status_code=400,
            detail="소셜 로그인 인증에 실패했습니다.",
        )


def auth_user_payload(
    user: User,
    login_provider: str,
    social_email: str | None = None,
) -> dict[str, Any]:
    return {
        "user_id": user.id,
        "username": None,
        "email": (
            social_email if login_provider != "LOCAL" else user.email
        ),
        "name": user.name,
        "login_provider": login_provider,
    }


def login_response(
    user: User,
    login_provider: str,
    social_email: str | None = None,
) -> dict[str, Any]:
    return {
        "message": "로그인에 성공했습니다.",
        "access_token": create_access_token(user, login_provider),
        "token_type": "bearer",
        "user": auth_user_payload(
            user,
            login_provider,
            social_email,
        ),
    }


def get_or_create_social_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str | None,
    name: str | None,
    profile_image_url: str | None,
) -> tuple[User, SocialAccount]:
    account = db.scalar(
        select(SocialAccount).where(
            SocialAccount.provider == provider,
            SocialAccount.provider_user_id == provider_user_id,
        )
    )
    if account is not None:
        return account.user, account

    internal_email = (
        f"{provider.lower()}_{provider_user_id}@oauth.local"
    )
    user = User(
        email=internal_email,
        name=name or f"{provider} 사용자",
        provider=provider,
        is_active=True,
    )
    account = SocialAccount(
        user=user,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        profile_image_url=profile_image_url,
    )
    db.add_all([user, account])
    db.commit()
    db.refresh(account)
    return user, account
