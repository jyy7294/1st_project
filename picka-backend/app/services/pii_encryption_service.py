from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


VERSION = "v1"


class PiiEncryptionConfigurationError(RuntimeError):
    pass


def _key() -> bytes:
    if not settings.pii_encryption_key:
        raise PiiEncryptionConfigurationError("PII_ENCRYPTION_KEY가 설정되지 않았습니다.")
    try:
        key = base64.urlsafe_b64decode(settings.pii_encryption_key.encode())
    except Exception as error:
        raise PiiEncryptionConfigurationError(
            "PII_ENCRYPTION_KEY는 URL-safe base64 형식이어야 합니다."
        ) from error
    if len(key) != 32:
        raise PiiEncryptionConfigurationError(
            "PII_ENCRYPTION_KEY는 디코딩했을 때 32바이트여야 합니다."
        )
    return key


def encrypt_text(value: str | None, *, context: str) -> str | None:
    if value is None:
        return None
    nonce = os.urandom(12)
    encrypted = AESGCM(_key()).encrypt(
        nonce,
        value.encode("utf-8"),
        context.encode("utf-8"),
    )
    return ":".join((
        VERSION,
        base64.urlsafe_b64encode(nonce).decode(),
        base64.urlsafe_b64encode(encrypted).decode(),
    ))


def decrypt_text(value: str | None, *, context: str) -> str | None:
    if value is None:
        return None
    try:
        version, nonce, encrypted = value.split(":", 2)
        if version != VERSION:
            raise ValueError("unsupported encryption version")
        plaintext = AESGCM(_key()).decrypt(
            base64.urlsafe_b64decode(nonce),
            base64.urlsafe_b64decode(encrypted),
            context.encode("utf-8"),
        )
        return plaintext.decode("utf-8")
    except PiiEncryptionConfigurationError:
        raise
    except Exception as error:
        raise ValueError("개인정보 암호문을 복호화할 수 없습니다.") from error


def encrypt_json(value: Any, *, context: str) -> str:
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return encrypt_text(serialized, context=context)


def decrypt_json(value: str | None, *, context: str) -> Any:
    plaintext = decrypt_text(value, context=context)
    return None if plaintext is None else json.loads(plaintext)
