"""ID 생성. 모든 테이블의 ID는 이 함수 하나로 만든다.

지금(개발 중): 접두어_순번  예) usr_001, revw_001
배포 전: DB를 초기화하고 접두어_랜덤(예: usr_reil4lk)으로 바꾼다. 그때 이 파일만 고치면 된다.

접두어 (팀 합의): usr(users), revw(reviews), run(review_runs),
               att(attachments), sub(legal_submissions), ntf(notifications), log(activity_logs)
"""

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

_PREFIX = re.compile(r"^[a-z]{2,8}$")


def new_id(db: Session, prefix: str) -> str:
    if not _PREFIX.match(prefix):
        raise ValueError(f"잘못된 ID 접두어: {prefix}")
    # 접두어마다 PostgreSQL 시퀀스(번호표 기계)를 하나씩 둔다. 동시에 요청해도 번호가 겹치지 않는다.
    seq = f"id_seq_{prefix}"
    db.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq}"))
    n = db.execute(text(f"SELECT nextval('{seq}')")).scalar_one()
    return f"{prefix}_{n:03d}"
