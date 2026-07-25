from __future__ import annotations

import argparse
from getpass import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import User
from app.services.auth_service import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(
        description="기존 사용자의 로컬 로그인 비밀번호를 안전하게 설정합니다."
    )
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass("새 비밀번호: ")
    confirmation = getpass("새 비밀번호 확인: ")
    if not password or password != confirmation:
        raise SystemExit("비밀번호가 비어 있거나 서로 일치하지 않습니다.")

    with SessionLocal() as db:
        from app.services.pii_encryption_service import email_blind_index
        user = db.scalar(
            select(User).where(
                User.email_blind_index == email_blind_index(args.email)
            )
        )
        if user is None:
            raise SystemExit("해당 이메일 사용자를 찾을 수 없습니다.")
        user.password_hash = hash_password(password)
        db.commit()
        print(f"{args.email} 사용자의 로컬 비밀번호를 설정했습니다.")


if __name__ == "__main__":
    main()
