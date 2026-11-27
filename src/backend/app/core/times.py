"""API 시각 규칙 (모든 API 공통).

- 저장: UTC 그대로 (timestamptz 칼럼, security.utcnow()). DB 시간대 설정은 바꾸지 않는다.
- 응답: 한국시간 ISO 8601, 초 단위. 예: 2026-11-27T09:45:16+09:00
  응답에 시각을 넣을 때는 반드시 to_kst()를 거친다. DB 시간대 설정(Asia/Seoul·UTC)에 따라
  결과가 달라지지 않게 하기 위해서다.
- 요청: 시각 파라미터에 오프셋이 없으면 한국시간으로 본다 (assume_kst()).
  예: from=2026-11-27T00:00:00 → 2026-11-27T00:00:00+09:00
- 날짜만 있는 값(YYYY-MM-DD 문자열, 예: 출처 effectiveDate)은 대상이 아니다.
- 목록 커서(pagination)는 내부 값이라 원래 정밀도 그대로 둔다.
"""

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def to_kst(dt: datetime | None) -> datetime | None:
    """응답용 시각. 한국시간, 초 단위. 시간대가 없는 값은 UTC로 저장된 값으로 본다."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST).replace(microsecond=0)


def assume_kst(dt: datetime | None) -> datetime | None:
    """요청으로 받은 시각. 오프셋이 없으면 한국시간으로 본다."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt
