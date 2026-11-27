"""개발용 테스트 계정 만들기. 로컬 개발(APP_ENV=local)에서만 실행된다.

실행 (src/backend 에서):
    uv run python -m app.seed_dev

이미 있는 이메일은 건너뛴다. 비밀번호는 모두 DEV_PASSWORD.
"""

import sys

from sqlalchemy import select

from app.admin_users.service import create_user
from app.core.config import settings
from app.core.db import SessionLocal
from app.models import User

DEV_PASSWORD = "adguard1234"
DEV_USERS = [
    ("개발 관리자", "admin@adguard.local", "ADMIN"),
    ("개발 마케팅", "marketing@adguard.local", "MARKETING"),
    ("개발 법무", "legal@adguard.local", "LEGAL"),
]


def seed() -> list[str]:
    created = []
    with SessionLocal() as db:
        for name, email, role in DEV_USERS:
            if db.scalar(select(User).where(User.email == email)) is not None:
                continue
            create_user(
                db, name=name, email=email, role=role, password=DEV_PASSWORD, must_change_password=False
            )
            created.append(email)
        db.commit()
    return created


def main() -> int:
    if settings.app_env != "local":  # 운영·스테이징 등 local이 아니면 모두 막는다
        print(f"개발용 시드는 APP_ENV=local에서만 실행할 수 있습니다. (지금: {settings.app_env})", file=sys.stderr)
        return 1
    created = seed()
    for email in created:
        print(f"만듦: {email}")
    print(f"완료. 새로 만든 계정 {len(created)}개, 비밀번호는 {DEV_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
