# 백엔드 검토 흐름·Agent 연동

- 담당: 검토 흐름·AI 연동 담당
- 기준: API 설계서 v5.2 (3장 실행 상태, 6장 검토 흐름·연동 방향·결과 보고서 조회, 7장 실행 상태와 공통 오류)
- 코드: `src/backend/app/reviews/`, `src/backend/app/agent/`
- 테스트: `src/backend/tests/` (가짜 Agent 기준 70개 통과)

## 1. API 목록

| 방향 | API | 설명 | 성공 |
|---|---|---|---|
| 프론트 → 백엔드 | `POST /api/v1/attachments` | 파일 첨부 (.pdf·.xlsx·.docx) | 201 |
| 프론트 → 백엔드 | `POST /api/v1/reviews` | 신규 검토. 검토 건과 AI 심의 실행을 만든다 | 202 |
| 프론트 → 백엔드 | `GET /api/v1/reviews/{reviewId}` | AI 검토 보고서 | 200 |
| 프론트 → 백엔드 | `POST /api/v1/reviews/{reviewId}/ra-runs` | AI 추천 요청 (RA_SUGGEST) | 202 |
| 프론트 → 백엔드 | `POST /api/v1/reviews/{reviewId}/ra-runs/{runId}/recheck` | 추천 문구 [재심의] (RA_RECHECK) | 202 |
| 프론트 → 백엔드 | `POST /api/v1/reviews/{reviewId}/ra-runs/{runId}/dismiss` | 추천 문구 [닫기] | 200 |
| 프론트 → 백엔드 | `GET /api/v1/review-runs/{runId}` | 실행 상태 (폴링) | 200 |
| 프론트 → 백엔드 | `POST /api/v1/review-runs/{runId}/retry` | 실패한 실행 [다시 검토] | 202 |
| 백엔드 → Agent | `POST {AGENT_URL}/internal/v1/review-jobs` | 작업 요청 | 202 |
| Agent → 백엔드 | `POST /internal/v1/review-runs/{runId}/completion` | 완료 통지 | 200 |
| Agent → 백엔드 | `GET /internal/v1/attachments/{attachmentId}?expires=..&sig=..` | 첨부 내려받기 (서명 URL, 10분) | 200 |

- 202 응답에는 `Location: /api/v1/review-runs/{runId}` 헤더가 붙는다.
- 실행을 만드는 API(reviews, ra-runs, recheck, retry)는 `Idempotency-Key`를 받는다. 같은 키로 다시 보내면 처음 응답을 그대로 돌려주고 Agent에도 한 번만 보낸다.
- 백엔드 ↔ Agent 사이 인증은 양쪽 모두 `Authorization: Bearer {AGENT_TOKEN}`이다.
- 길이 제한(DB 칼럼 길이): 제목 200자, 첨부 파일 이름 255자, 완료 통지 `error.code` 50자. 넘으면 422 VALIDATION_ERROR (`title`·`file`·`error.code` INVALID).
- 응답 시각은 한국시간 ISO 8601, 초 단위다 (예: `2026-11-27T09:45:16+09:00`). 모든 API 공통 규칙으로, `app/core/times.py`의 `to_kst()`로 바꾼다. 저장은 UTC 그대로이고, 오프셋 없이 받은 요청 시각은 한국시간으로 본다.

## 2. 실행 상태

```
POST /reviews · ra-runs · recheck · retry
        │  (202, QUEUED)
        ▼
     QUEUED ──(Agent가 작업 요청을 202로 접수)──▶ RUNNING ──(완료 통지)──▶ SUCCEEDED / FAILED
        │                                           │
        └─(작업 요청 3번 모두 실패)─▶ FAILED          └─(실행을 만든 뒤 180초)─▶ FAILED
              AGENT_UNAVAILABLE                          RUN_TIMEOUT
```

| 단계 (stage) | 성공하면 저장되는 것 | 보고서 버전 |
|---|---|---|
| AI_SCREENING (AI 심의) | 보고서 | v1 |
| RA_SUGGEST (추천 문구 생성) | `review_runs.suggestion` {text, rationale, status=PENDING}. 판정 없음 | 그대로 |
| RA_RECHECK (재심의) | 보고서. 심의한 문구 = 확인한 추천 문구 | +1 |

### 버튼 (allowedActions)

검토 건의 상태는 따로 저장하지 않고, 최근 실행·최신 보고서·최근 법무 요청에서 계산한다.

| 상태 | allowedActions |
|---|---|
| 끝남, 실행 중, 작성자가 아님 | `[]` |
| 실패, 재시도 가능 | `RETRY_RUN` (+ 보고서가 있으면 `CANCEL`) |
| 실패, 재시도 불가 (`error.retryable=false`) | `CANCEL` |
| 확인 대기 추천 문구 있음 | `RECHECK_SUGGESTION`, `DISMISS_SUGGESTION` |
| 최신 보고서로 법무 요청 후 검토 대기·검토 중 | `[]` |
| 최신 보고서로 검토 의견 받음 | `PUBLISH`, `RUN_RA`, `CANCEL` |
| 적합 | `SEND_TO_LEGAL`, `END` |
| 부적합 | `RUN_RA`, `CANCEL` |

## 3. 백엔드 → Agent 작업 요청 예시

`POST {AGENT_URL}/internal/v1/review-jobs`, `Authorization: Bearer {AGENT_TOKEN}`. Agent는 접수하면 **202**를 준다.

### AI_SCREENING

```json
{
  "schemaVersion": "1.0",
  "runId": "run_001",
  "reviewId": "revw_001",
  "stage": "AI_SCREENING",
  "title": "면역력 강화 음료 광고",
  "productCategory": "GENERAL_FOOD",
  "text": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.",
  "attachments": [
    {"attachmentId": "att_001", "filename": "근거자료.pdf",
     "url": "http://localhost:8000/internal/v1/attachments/att_001?expires=1795688778&sig=..."}
  ],
  "baseReportRunId": null,
  "baseReport": null,
  "legalOpinion": null
}
```

### RA_SUGGEST

`text`는 원문이다. `baseReportRunId`·`baseReport`(최신 보고서, 응답의 `report`와 같은 형식)와 `legalOpinion`(최신 보고서에 검토 의견을 받았으면 그 내용, 아니면 null)을 함께 보낸다.

```json
{
  "schemaVersion": "1.0", "runId": "run_002", "reviewId": "revw_001", "stage": "RA_SUGGEST",
  "title": "면역력 강화 음료 광고", "productCategory": "GENERAL_FOOD",
  "text": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.",
  "attachments": [],
  "baseReportRunId": "run_001",
  "baseReport": {"runId": "run_001", "stage": "AI_SCREENING", "version": 1,
                 "reviewedText": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.",
                 "decision": "UNSUITABLE", "summary": "...", "improvementNote": "...", "findings": ["..."]},
  "legalOpinion": null
}
```

### RA_RECHECK

`text` 자리에 마케팅 담당자가 [재심의]한 추천 문구가 들어간다. 이 실행을 재시도해도 같은 추천 문구를 보낸다.

```json
{
  "schemaVersion": "1.0", "runId": "run_003", "reviewId": "revw_001", "stage": "RA_RECHECK",
  "text": "하루 한 포, 맛있게 즐기는 건강한 습관.",
  "baseReportRunId": "run_001", "baseReport": {"...": "..."}, "legalOpinion": null
}
```

## 4. Agent → 백엔드 완료 통지 예시

`POST /internal/v1/review-runs/{runId}/completion`, `Authorization: Bearer {AGENT_TOKEN}`.

### 성공 (AI_SCREENING·RA_RECHECK): report

```json
{
  "schemaVersion": "1.0",
  "reviewId": "revw_001",
  "runStatus": "SUCCEEDED",
  "report": {
    "decision": "UNSUITABLE",
    "summary": "일반식품에 기능성 표현이 있습니다.",
    "improvementNote": "‘면역력 개선’ 같은 기능성 표현을 빼 주세요.",
    "findings": [
      {
        "sentenceId": "s1",
        "text": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.",
        "decision": "UNSUITABLE",
        "rationale": "일반식품은 면역력 개선 등 기능성을 표시할 수 없습니다.",
        "violationCode": "3",
        "sources": [
          {"title": "식품 등의 표시·광고에 관한 법률", "reference": "제8조 제1항", "url": null,
           "lawText": "누구든지 ...", "noticeNo": null, "effectiveDate": null}
        ],
        "referenceCases": [
          {"title": "일반식품 면역 기능성 표방 광고", "summary": "시정명령", "caseRef": null, "caseDate": null, "url": null}
        ],
        "alternativeText": "맛과 원료 중심으로 표현해 보세요."
      }
    ]
  }
}
```

### 성공 (RA_SUGGEST): suggestion

```json
{"schemaVersion": "1.0", "reviewId": "revw_001", "runStatus": "SUCCEEDED",
 "suggestion": {"text": "하루 한 포, 맛있게 즐기는 건강한 습관.", "rationale": "기능성 표현을 빼고 섭취 습관 중심으로 바꿨습니다."}}
```

### 실패

```json
{"schemaVersion": "1.0", "reviewId": "revw_001", "runStatus": "FAILED",
 "error": {"code": "SEARCH_FAILED", "message": "검색 서버 응답이 없습니다.", "retryable": true}}
```

- `retryable=true`: 일시적 문제. 화면에 [다시 검토]가 나온다.
- `retryable=false`: 입력 문제라 다시 해도 같은 결과. [심의 취소]만 나오고 retry는 409다.

### 응답 (200)

실행 상태 조회(`GET /review-runs/{runId}`)와 같은 모양이다.

```json
{"reviewId": "revw_001", "runId": "run_001", "stage": "AI_SCREENING", "runStatus": "SUCCEEDED", "attempt": 1,
 "updatedAt": "2026-11-26T19:16:19+09:00", "startedAt": "2026-11-26T19:16:18+09:00",
 "finishedAt": "2026-11-26T19:16:19+09:00", "error": null}
```

## 5. 보고서 저장 형식

`reports` 테이블 (실행 1번 = 보고서 1개, `(review_id, version)` UNIQUE)

| 칼럼 | 값 |
|---|---|
| `run_id` (PK) | 완료 통지를 보낸 실행 |
| `stage` | AI_SCREENING 또는 RA_RECHECK |
| `version` | 같은 검토 건의 직전 버전 + 1, 처음은 1. **백엔드가 채운다** |
| `reviewed_text` | 이 버전에서 심의한 문구. AI 심의는 원문(`reviews.text`), 재심의는 [재심의]한 추천 문구. **백엔드가 채운다** |
| `decision`, `summary`, `improvement_note` | 완료 통지의 report 값 |
| `findings` (JSONB) | 완료 통지의 `report.findings[]`를 camelCase 그대로 저장 |

- 추천 문구 생성(RA_SUGGEST)은 보고서를 만들지 않는다. `review_runs.suggestion`에 `{text, rationale, status}`를 저장한다. status는 PENDING → RECHECKED(재심의) 또는 DISMISSED(닫기)로 바뀐다.
- Agent가 `version`·`reviewedText`를 보내도 무시한다.
- 재심의 문구: `review_runs`에 입력 문구 칼럼이 아직 없어서, 재시도 사슬의 최초 RA_RECHECK 실행 직전에 [재심의] 처리된 RA_SUGGEST 실행의 `suggestion.text`를 쓴다. 칼럼(`review_runs.input_text`)은 추가하기로 합의했고, 인증·공통 기반 담당이 추가하면 그 값을 쓰도록 바꾼다.
- `attachments.content_type`: 파일 종류 `pdf`·`xlsx`·`docx`. Agent가 내려받을 때 MIME 타입(`application/pdf` 등)으로 바꿔 응답한다.

## 6. 완료 통지 검증 규칙

어기면 **422 VALIDATION_ERROR**이고, `fieldErrors`에 어긴 곳을 모두 담는다.

| 규칙 | fieldErrors 예 |
|---|---|
| 공통 필수: schemaVersion, reviewId, runStatus | `schemaVersion` REQUIRED |
| schemaVersion은 `"1.0"`만 | `schemaVersion` INVALID |
| SUCCEEDED → report 필수, error 없음 | `report` REQUIRED, `error` INVALID |
| RA_SUGGEST의 SUCCEEDED → report 대신 suggestion | `suggestion` REQUIRED, `report` INVALID |
| FAILED → error 필수, report·suggestion 없음 | `error` REQUIRED, `report` INVALID |
| report 필수: decision, summary, findings(1개 이상) | `report.findings` REQUIRED |
| 문장 필수: sentenceId, text, decision, rationale, sources(배열), referenceCases(배열) | `report.findings[0].rationale` REQUIRED |
| 출처 필수: title, reference / 참고 사례 필수: title, summary | `report.findings[0].sources[0].reference` REQUIRED |
| suggestion 필수: text, rationale | `suggestion.rationale` REQUIRED |
| error 필수: code, message, retryable | `error.retryable` REQUIRED |
| error.code는 50자까지 (message는 500자에서 자름) | `error.code` INVALID |
| 전체 판정: 한 문장이라도 UNSUITABLE이면 UNSUITABLE | `report.decision` INVALID |
| 부적합 문장은 sources 1개 이상 | `report.findings[0].sources` REQUIRED |
| 부적합 문장은 violationCode 필수, 부록 D 코드만 | `report.findings[0].violationCode` REQUIRED / INVALID |
| 적합 문장의 violationCode는 null | `report.findings[0].violationCode` INVALID |

- 빈 값 = 누락, null, 빈 문자열, 공백만 있는 문자열 → REQUIRED.
- null을 허용하는 필드(improvementNote, alternativeText, sources[].url·lawText·noticeNo·effectiveDate, referenceCases[].caseRef·caseDate·url)에 빈 문자열을 보내면 INVALID다. 값이 없으면 null로 보낸다.
- 422를 받은 실행은 상태가 그대로라서 고쳐서 다시 보내면 저장된다.

## 7. 오류 처리 규칙

| 상황 | 백엔드 처리 |
|---|---|
| 작업 요청이 연결 오류·응답 없음·202가 아님 | 같은 runId로 다시 보낸다 (1초 간격, 모두 3번). 3번 다 실패하면 FAILED / `AGENT_UNAVAILABLE` (retryable=true) |
| 실행을 만든 뒤 180초 안에 완료 통지 없음 | FAILED / `RUN_TIMEOUT` (retryable=true). QUEUED도 포함 |
| 완료 통지의 토큰이 없거나 틀림 | 401 UNAUTHENTICATED |
| 없는 runId, 또는 reviewId가 실행과 다름 | 404 NOT_FOUND |
| 이미 확정된 실행에 같은 runStatus로 다시 옴 (중복) | 200. 처음 결과 그대로 두고 다시 처리하지 않음 |
| 이미 확정된 실행에 다른 runStatus가 옴 | 409 STATE_CONFLICT |
| 시간 초과 뒤 늦게 SUCCEEDED가 옴 (지연) | 409 STATE_CONFLICT. RUN_TIMEOUT을 덮어쓰지 않음 |
| 202보다 완료 통지가 먼저 옴 | 정상 처리 (QUEUED → SUCCEEDED, startedAt도 기록) |
| 재시도: 최신 실패 실행이 아님 / 실행 중 | 409 STATE_CONFLICT |
| 재시도: retryable=false | 409 STATE_CONFLICT |
| 재시도: 최초 실행별 2회를 다 씀 (attempt 3) | 409 RETRY_LIMIT_REACHED |

- Agent가 완료 통지를 보냈는데 응답을 못 받았으면 같은 내용으로 다시 보내면 된다 (중복은 200).
- 시간 초과는 따로 돌아가는 작업 없이, 실행·보고서를 조회하거나 완료 통지를 받을 때 확인해서 확정한다. 상태는 API로만 보이므로 결과는 같다.
- 목록·대시보드처럼 여러 건을 보여 주는 API는 조회 전에 `app/reviews/runs.py`의 `expire_overdue_runs(db)`를 한 번 부른다. 그래야 180초가 지난 실행이 "검토 중"으로 남지 않는다.

## 8. 확인 결과

### 가짜 Agent 테스트 (`uv run pytest tests`, 70개 통과)

진짜 Agent 대신 작업 요청을 기록만 하는 가짜 Agent를 끼우고, 완료 통지는 테스트가 Agent 대신 보낸다.

| 구분 | 확인한 것 | 파일 |
|---|---|---|
| 정상 완료 | 202 + Location, 작업 요청 본문, QUEUED → RUNNING → SUCCEEDED, 보고서 v1, 버튼, REPORT_VIEWED 로그 | test_review_flow.py |
| AI 추천·재심의 | 추천 문구 저장·팝업 버튼, [재심의] 시 추천 문구로 작업 요청, v2·reviewedText·previousReport, 알림 RA_SUGGESTED·RA_COMPLETED, [닫기] 후 버튼 복귀, 검토 의견이 legalOpinion으로 전달 | test_review_flow.py |
| 실패 | retryable=true → RETRY_RUN, false → CANCEL만, AI 추천 실패 시 보고서 유지 | test_run_failures.py |
| 재시도 | 새 runId·attempt+1, 최초 실행별 2회 한도(409 RETRY_LIMIT_REACHED), 최신 실패 실행만, 재심의 재시도는 같은 추천 문구 | test_run_failures.py |
| Agent 연결 불가 | 같은 runId로 3번 보낸 뒤 AGENT_UNAVAILABLE, 재시도하면 정상 | test_run_failures.py |
| 시간 초과 | 179초 RUNNING, 181초 RUN_TIMEOUT (실행 조회·보고서 조회 둘 다), 목록용 `expire_overdue_runs` | test_run_failures.py |
| 지연 완료 통지 | 시간 초과 뒤 SUCCEEDED → 409, 보고서 저장 안 됨 / FAILED → 200 무시 | test_run_failures.py |
| 중복 완료 통지 | 같은 상태 → 200, 처음 결과 유지 / 다른 상태 → 409 / 추천 문구 중복도 처음 것 유지 | test_run_failures.py |
| 검증 규칙 | 6장 표의 모든 규칙과 fieldErrors 경로, 토큰 401, runId·reviewId 404, 제목 200자 초과 422 | test_completion_validation.py, test_review_flow.py |
| 첨부 | 업로드 201·415·413, 파일 이름 255자 초과 422, 합계 10MB, 남의 파일·없는 파일·이미 쓴 파일 422, 서명 URL 다운로드(MIME 응답)·위조 401 | test_attachments.py |
| 시각 형식 | 검토·실행·관리자 API 모두 `+09:00` 초 단위 (테스트 DB를 UTC로 두고 확인), 오프셋 없는 `from`/`to`는 한국시간 | test_times.py |
| 중복 클릭 | 같은 Idempotency-Key → 같은 runId, 작업 요청 1번 / 다른 내용 → 409 | test_review_flow.py |
| 검토 접수 | 미로그인·비활성 계정 401, 잘못된 제품 분류 422, 저장 중 오류 시 검토 건·첨부 연결·실행·활동 로그·멱등성 키 모두 롤백(Agent 요청 없음, 같은 키로 다시 보내면 정상 접수) | test_review_request.py |

### HTTP 연결 확인

실제 서버와 HTTP로 동작하는 가짜 Agent 서버를 따로 띄워서 확인했다. 결과는 다음과 같다.

- AI 심의(부적합 v1) → AI 추천 → 재심의(적합 v2)가 끝까지 동작했다.
- 작업 요청(`httpx`)과 완료 통지가 서버 사이에서 실제로 오갔다.
- Agent가 서명 URL로 첨부 파일을 내려받았다.

### 아직 못 한 것

- **진짜 Agent와의 연동 확인**: Agent 서버가 준비되면 같은 시나리오를 다시 돌린다.
