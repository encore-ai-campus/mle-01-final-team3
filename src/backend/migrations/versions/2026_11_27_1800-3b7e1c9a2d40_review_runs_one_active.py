"""review_runs: 광고 건당 실행 중(QUEUED·RUNNING) 실행 1개만

설계서 3장 '광고 건당 실행 중 작업 1개만 허용'을 DB 제약으로 보장한다.
같은 review_id에 QUEUED·RUNNING 실행이 이미 있으면 새 실행 저장이 실패한다.

적용 전 확인: 아래 쿼리 결과가 있으면 인덱스 생성이 실패하므로 먼저 정리해야 한다.
    SELECT review_id, COUNT(*) FROM review_runs
    WHERE status IN ('QUEUED', 'RUNNING') GROUP BY review_id HAVING COUNT(*) > 1;

Revision ID: 3b7e1c9a2d40
Revises: 844f6c112613
Create Date: 2026-11-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3b7e1c9a2d40'
down_revision: Union[str, Sequence[str], None] = '844f6c112613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "uq_review_runs_one_active",
        "review_runs",
        ["review_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_review_runs_one_active", table_name="review_runs")
