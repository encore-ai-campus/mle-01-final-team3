"""검토 흐름에서 쓰는 코드 값. DB에는 문자열로 저장한다 (models.py 참고)."""

# 실행 단계 (review_runs.stage)
AI_SCREENING = "AI_SCREENING"  # AI 심의 → 보고서
RA_SUGGEST = "RA_SUGGEST"  # AI 추천 문구 생성 → 추천 문구만 (판정 없음)
RA_RECHECK = "RA_RECHECK"  # 재심의: 확인한 추천 문구를 AI 심의와 같은 흐름으로 판정 → 보고서 (버전 +1)

# 실행 상태 (review_runs.status)
QUEUED = "QUEUED"
RUNNING = "RUNNING"
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"
ACTIVE = (QUEUED, RUNNING)

# 판정
SUITABLE = "SUITABLE"
UNSUITABLE = "UNSUITABLE"
DECISION_LABEL = {SUITABLE: "적합", UNSUITABLE: "부적합"}

# 추천 문구 상태 (review_runs.suggestion.status)
SUGGESTION_PENDING = "PENDING"  # 확인 대기
SUGGESTION_RECHECKED = "RECHECKED"  # [재심의]
SUGGESTION_DISMISSED = "DISMISSED"  # [닫기]

# 법무 처리 상태 (legal_submissions.status)
OPINION_SENT = "OPINION_SENT"

# 화면 버튼 (allowedActions)
RUN_RA = "RUN_RA"
RETRY_RUN = "RETRY_RUN"
SEND_TO_LEGAL = "SEND_TO_LEGAL"
END = "END"
PUBLISH = "PUBLISH"
CANCEL = "CANCEL"
RECHECK_SUGGESTION = "RECHECK_SUGGESTION"
DISMISS_SUGGESTION = "DISMISS_SUGGESTION"

# 재시도: 최초 실행별 최대 2회 → attempt는 최대 3
MAX_ATTEMPT = 3

# 백엔드가 붙이는 실패 코드 (설계서 7장 '실패 코드')
RUN_TIMEOUT = "RUN_TIMEOUT"
AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"

# 완료 통지 schemaVersion 지원 값
SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

# 위반 유형 코드 (별표 1 호-목, 설계서 부록 D)
VIOLATION_CODES = frozenset({
    "1-가", "1-나", "1-다", "1-라", "2-가", "2-다", "2-라",
    "3", "4-가", "4-나", "4-라", "4-마",
    "5-나", "5-다", "5-라", "5-아", "5-자", "5-차", "5-카",
    "6", "7-가", "7-나", "8", "법8-1-10",
})  # fmt: skip
