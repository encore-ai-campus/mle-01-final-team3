"""erd v0.5: reviews channel main_ingredients, review_runs input_text

설계서 v5.3 · ERD v0.5에서 늘어난 칸 3개.
- reviews.channel: 게시 채널 (DETAIL_PAGE·SNS·BANNER). 필수.
  이미 있는 검토 건은 값이 없으므로 DETAIL_PAGE로 채운 뒤 기본값은 지운다 (새 건은 API가 반드시 넣는다).
- reviews.main_ingredients: 주요 원료명 배열. 없으면 [].
- review_runs.input_text: 재심의(RA_RECHECK) 실행이 심의한 추천 문구. 다른 단계는 null.

Revision ID: 844f6c112613
Revises: 65c4403ed32d
Create Date: 2026-11-27 12:24:42.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '844f6c112613'
down_revision: Union[str, Sequence[str], None] = '65c4403ed32d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reviews', sa.Column('channel', sa.String(length=32), server_default='DETAIL_PAGE', nullable=False))
    op.alter_column('reviews', 'channel', server_default=None)
    op.add_column(
        'reviews',
        sa.Column('main_ingredients', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    )
    op.add_column('review_runs', sa.Column('input_text', sa.Text(), nullable=True))
    # 이미 있는 재심의 실행은 [재심의]한 추천 문구(직전 RA_SUGGEST의 suggestion.text)를 채운다. 재시도는 사슬의 첫 실행 기준.
    op.execute("""
        WITH RECURSIVE chain AS (
            SELECT id, id AS root_id, review_id FROM review_runs WHERE stage = 'RA_RECHECK' AND retry_of IS NULL
            UNION ALL
            SELECT r.id, c.root_id, r.review_id FROM review_runs r JOIN chain c ON r.retry_of = c.id
        )
        UPDATE review_runs t
        SET input_text = (
            SELECT s.suggestion->>'text' FROM review_runs s, review_runs root
            WHERE root.id = c.root_id AND s.review_id = c.review_id AND s.stage = 'RA_SUGGEST'
              AND s.created_at <= root.created_at AND s.suggestion->>'status' = 'RECHECKED'
            ORDER BY s.created_at DESC LIMIT 1
        )
        FROM chain c WHERE t.id = c.id
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('review_runs', 'input_text')
    op.drop_column('reviews', 'main_ingredients')
    op.drop_column('reviews', 'channel')
