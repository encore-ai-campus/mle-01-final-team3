"""운영용 명령. 첫 ADMIN 계정을 만든다.

실행 (src/backend 에서):
    uv run python -m app.cli create-admin --email admin@회사.com --name 관리자

임시 비밀번호를 화면에 한 번만 보여 준다. 첫 로그인 후 비밀번호를 바꾸도록 안내된다.
"""

import argparse
import sys

from app.admin_users.service import create_user
from app.core.db import SessionLocal
from app.core.errors import ApiError
from app.core.security import generate_temporary_password


def create_admin(email: str, name: str) -> tuple[str, str]:
    """ADMIN을 만들고 (userId, 임시 비밀번호)를 돌려준다."""
    password = generate_temporary_password()
    with SessionLocal() as db:
        user = create_user(db, name=name, email=email, role="ADMIN", password=password)
        db.commit()
        return user.id, password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-admin", help="ADMIN 계정 만들기 (임시 비밀번호 발급)")
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    args = parser.parse_args(argv)

    if args.command == "create-admin":
        try:
            user_id, password = create_admin(args.email, args.name)
        except ApiError as e:
            print(f"실패: {e.message}", file=sys.stderr)
            return 1
        print(f"ADMIN 계정을 만들었습니다: {user_id} ({args.email})")
        print(f"임시 비밀번호: {password}")
        print("이 비밀번호는 다시 보여 주지 않습니다. 첫 로그인 후 바로 변경해 주세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
