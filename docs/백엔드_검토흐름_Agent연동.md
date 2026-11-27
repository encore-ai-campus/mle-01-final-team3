# 백엔드 검토 흐름·Agent 연동

- 담당: 검토 흐름·AI 연동 담당
- 기준: API 설계서 v5.3 (3장 실행 상태, 6장 검토 흐름·연동 방향·결과 보고서 조회, 7장 실행 상태와 공통 오류) + Agent 담당과 정한 것(9장)
- 코드: `src/backend/app/reviews/`, `src/backend/app/agent/`
- 테스트: `src/backend/tests/` (가짜 Agent 기준 94개 통과)

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
| 백엔드 → Agent | `POST {AGENT_URL}/internal/v1/review-jobs` | 작업 요청 | 202 (이미 끝난 runId는 200) |
| Agent → 백엔드 | `POST /internal/v1/review-runs/{runId}/completion` | 완료 통지 | 200 |
| Agent → 백엔드 | `GET /internal/v1/attachments/{attachmentId}?expires=..&sig=..` | 첨부 내려받기 (서명 URL, 10분) | 200 |

- 202 응답에는 `Location: /api/v1/review-runs/{runId}` 헤더가 붙는다.
- 실행을 만드는 API(reviews, ra-runs, recheck, retry)는 `Idempotency-Key`를 받는다. 같은 키로 다시 보내면 처음 응답을 그대로 돌려주고 Agent에도 한 번만 보낸다.
- 백엔드 ↔ Agent 사이 인증은 양쪽 모두 `Authorization: Bearer {AGENT_TOKEN}`이다. 토큰을 바꾸는 동안에는 `AGENT_TOKEN_EXTRA`도 받는다 (7장 '서비스 토큰 교체').
- 길이 제한(DB 칼럼 길이): 제목 200자, 첨부 파일 이름 255자, 완료 통지 `error.code` 50자. 넘으면 422 VALIDATION_ERROR (`title`·`file`·`error.code` INVALID).
- 응답 시각은 한국시간 ISO 8601, 초 단위다 (예: `2026-11-27T09:45:16+09:00`). 모든 API 공통 규칙으로, `app/core/times.py`의 `to_kst()`로 바꾼다. 저장은 UTC 그대로이고, 오프셋 없이 받은 요청 시각은 한국시간으로 본다.

## 2. 실행 상태

```
POST /reviews · ra-runs · recheck · retry
        │  (202, QUEUED)
        ▼
     QUEUED ──(Agent가 작업 요청을 202·200으로 접수)──▶ RUNNING ──(완료 통지)──▶ SUCCEEDED / FAILED
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

`POST {AGENT_URL}/internal/v1/review-jobs`, `Authorization: Bearer {AGENT_TOKEN}`.

### Agent 응답 (Agent 담당과 합의)

같은 runId가 다시 와도 Agent는 작업을 두 번 실행하지 않는다. 앞 요청의 응답이 중간에 끊기면 백엔드가 같은 runId로 다시 보내기 때문이다.

| Agent 쪽 상황 | Agent 응답 | 백엔드 처리 |
|---|---|---|
| 처음 받음, 또는 같은 runId를 이미 진행 중 | **202** | 접수. QUEUED → RUNNING |
| 이미 성공·실패했고 완료 통지도 보냄 | **200** + 현재 상태. 다시 실행하지 않음 | 접수로 보고 다시 보내지 않음. 200 본문은 쓰지 않음 (결과는 완료 통지로만 받는다) |
| 실행은 끝났는데 완료 통지를 못 보냄 | **200**, 저장해 둔 같은 결과를 완료 통지로 다시 보냄 | 위와 같음. 완료 통지가 오면 정상 저장 |
| 그 밖의 응답, 연결 오류, 10초 안에 응답 없음 | - | 같은 runId로 다시 보냄 (모두 3번). 3번 다 실패하면 FAILED / `AGENT_UNAVAILABLE` |

### 필드

| 필드 | 값 |
|---|---|
| `schemaVersion`, `runId`, `reviewId`, `stage` | 실행 정보. stage는 AI_SCREENING·RA_SUGGEST·RA_RECHECK |
| `title`, `productCategory` | 제품명, 제품 분류 (HEALTH_FUNCTIONAL_FOOD·GENERAL_FOOD·CHILDREN_PREFERRED_FOOD) |
| `channel` | 게시 채널: DETAIL_PAGE·SNS·BANNER (필수) |
| `mainIngredients` | 주요 원료명 배열. 없으면 `[]` |
| `text` | 이번에 심의할 문구. AI 심의·AI 추천은 원문, 재심의는 [재심의]한 추천 문구 |
| `attachments[]` | `attachmentId`, `filename`, `url`(서명 URL, 10분) |
| `baseReportRunId`, `baseReport` | RA_SUGGEST·RA_RECHECK: 최신 보고서 (응답의 `report`와 같은 형식). AI 심의는 null |
| `initialReport` | RA_SUGGEST만: 최초 AI 심의 보고서(v1, `baseReport`와 같은 형식). 최신 보고서가 v1이면(재심의 전) null. 다른 단계는 null |
| `legalOpinion` | RA_SUGGEST만: 최신 보고서로 법무 검토 의견을 받았으면 그 내용, 아니면 null |

### AI_SCREENING

```json
{
  "schemaVersion": "1.0",
  "runId": "run_001",
  "reviewId": "revw_001",
  "stage": "AI_SCREENING",
  "title": "면역력 강화 음료 광고",
  "productCategory": "GENERAL_FOOD",
  "channel": "DETAIL_PAGE",
  "mainIngredients": ["홍삼", "비타민C"],
  "text": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.",
  "attachments": [
    {"attachmentId": "att_001", "filename": "근거자료.pdf",
     "url": "http://localhost:8000/internal/v1/attachments/att_001?expires=1795688778&sig=..."}
  ],
  "baseReportRunId": null,
  "baseReport": null,
  "initialReport": null,
  "legalOpinion": null
}
```

### RA_SUGGEST

`text`는 원문이다. 최신 보고서(`baseReport`)에 직전 검토 문구(`reviewedText`)와 그 리젝 근거(`findings[]`)가 있다. 재심의를 한 번 이상 거친 뒤(최신이 v2 이상)에는 최초 원문의 리젝 근거를 볼 수 있게 `initialReport`(v1)도 보낸다.

```json
{
  "schemaVersion": "1.0", "runId": "run_004", "reviewId": "revw_001", "stage": "RA_SUGGEST",
  "title": "면역력 강화 음료 광고", "productCategory": "GENERAL_FOOD",
  "channel": "DETAIL_PAGE", "mainIngredients": ["홍삼", "비타민C"],
  "text": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.",
  "attachments": [],
  "baseReportRunId": "run_003",
  "baseReport": {"runId": "run_003", "stage": "RA_RECHECK", "version": 2,
                 "reviewedText": "하루 한 포, 맛있게 즐기는 건강한 습관.",
                 "decision": "UNSUITABLE", "summary": "...", "improvementNote": "...", "findings": ["..."]},
  "initialReport": {"runId": "run_001", "stage": "AI_SCREENING", "version": 1,
                    "reviewedText": "하루 한 포로 면역력 개선에 도움을 줄 수 있습니다.",
                    "decision": "UNSUITABLE", "summary": "...", "improvementNote": "...", "findings": ["..."]},
  "legalOpinion": null
}
```

### RA_RECHECK

`text` 자리에 마케팅 담당자가 [재심의]한 추천 문구가 들어간다 (`review_runs.input_text`에 저장). 이 실행을 재시도해도 같은 추천 문구를 보낸다.

```json
{
  "schemaVersion": "1.0", "runId": "run_003", "reviewId": "revw_001", "stage": "RA_RECHECK",
  "text": "하루 한 포, 맛있게 즐기는 건강한 습관.",
  "baseReportRunId": "run_001", "baseReport": {"...": "..."}, "initialReport": null, "legalOpinion": null
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

실패 코드는 Agent가 정한다 (설계서 7장: 백엔드가 정하는 코드는 `RUN_TIMEOUT`·`AGENT_UNAVAILABLE`뿐). 첨부 관련 코드는 Agent 담당과 이렇게 정했다.

| error.code | 언제 | retryable |
|---|---|---|
| `ATTACHMENT_DOWNLOAD_FAILED` | 내려받기의 일시적 실패: 서명 URL 만료, 네트워크 오류, 파일 서버 5xx | `true` (다시 검토하면 새 실행·새 URL) |
| `INVALID_INPUT` | 파일 자체의 문제: 손상, 지원하지 않는 형식, 내용을 읽을 수 없음 | `false` |

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
- 재심의 문구: [재심의]할 때 추천 문구를 `review_runs.input_text`에 저장하고, 재시도하면 그대로 복사한다. 재심의 보고서의 `reviewed_text`도 이 값이다. 다른 단계는 null.
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
| 작업 요청이 연결 오류·응답 없음·202·200이 아님 | 같은 runId로 다시 보낸다 (1초 간격, 모두 3번). 3번 다 실패하면 FAILED / `AGENT_UNAVAILABLE` (retryable=true) |
| 작업 요청에 Agent가 200 (이미 끝난 runId) | 접수로 보고 다시 보내지 않는다. 결과는 완료 통지로 받는다 |
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

### 서비스 토큰 교체

같은 토큰을 양방향으로 쓰므로, 서비스를 멈추지 않고 바꾸려면 교체하는 동안 이전 토큰과 새 토큰을 둘 다 받는다. 토큰은 양쪽 서버의 `.env`에만 두고 git·메신저에 올리지 않는다. 노출이 의심되면 바로 이 절차로 바꾼다.

| 단계 | 백엔드 `.env` | Agent |
|---|---|---|
| 평소 | `AGENT_TOKEN=이전`, `AGENT_TOKEN_EXTRA=` (비움) | 이전 토큰으로 보내고 받음 |
| 1. 새 토큰을 받는 토큰에 추가 | `AGENT_TOKEN=이전`, `AGENT_TOKEN_EXTRA=새` | 이전·새 토큰 모두 받음 |
| 2. 보내는 토큰을 새 토큰으로 | `AGENT_TOKEN=새`, `AGENT_TOKEN_EXTRA=이전` | 새 토큰으로 보냄 |
| 3. 이전 토큰 지우기 (2단계 뒤 10분 이상 지나서) | `AGENT_TOKEN=새`, `AGENT_TOKEN_EXTRA=` (비움) | 이전 토큰을 받지 않음 |

- 백엔드는 `.env`를 바꾼 뒤 서버를 다시 시작해야 적용된다.
- 백엔드: `AGENT_TOKEN`으로 작업 요청을 보내고 첨부 URL에 서명한다. 완료 통지와 첨부 다운로드는 `AGENT_TOKEN`·`AGENT_TOKEN_EXTRA` 둘 다 받는다.
- 3단계를 10분 뒤에 하는 이유: 2단계 직전에 이전 토큰으로 서명한 첨부 URL이 10분 동안 유효하기 때문이다.
- 다음 단계로 넘어가기 전에 양쪽이 이전 단계를 마쳤는지 확인한다.

### 서명 URL과 로그

- 서버 접속 로그(uvicorn)는 첨부 다운로드 주소의 서명을 `sig=***`로 가려서 남긴다 (`app/reviews/attachments.py`의 `HideSignature`, `app/main.py`에서 붙임).
- Agent도 로그와 오류 메시지에 전체 URL 대신 `attachmentId`만 남긴다.

## 8. 확인 결과

### 가짜 Agent 테스트 (`uv run pytest tests`, 94개 통과)

진짜 Agent 대신 작업 요청을 기록만 하는 가짜 Agent를 끼우고, 완료 통지는 테스트가 Agent 대신 보낸다.

| 구분 | 확인한 것 | 파일 |
|---|---|---|
| 정상 완료 | 202 + Location, 작업 요청 본문(channel·mainIngredients 포함), QUEUED → RUNNING → SUCCEEDED, 보고서 v1, 버튼, REPORT_VIEWED 로그 | test_review_flow.py |
| AI 추천·재심의 | 추천 문구 저장·팝업 버튼, [재심의] 시 추천 문구로 작업 요청, v2·reviewedText·previousReport, 알림 RA_SUGGESTED·RA_COMPLETED, [닫기] 후 버튼 복귀, 검토 의견이 legalOpinion으로 전달, 재심의 뒤 AI 추천에 initialReport(v1) 전달 | test_review_flow.py |
| 실패 | retryable=true(SEARCH_FAILED·ATTACHMENT_DOWNLOAD_FAILED) → RETRY_RUN, false(INVALID_INPUT) → CANCEL만, AI 추천 실패 시 보고서 유지 | test_run_failures.py |
| Agent 응답 | 작업 요청에 202·200 → 접수(다시 보내지 않음, RUNNING), 400·401·409·500·503 → 실패로 보고 재전송 | test_agent_integration.py |
| 토큰 교체 | AGENT_TOKEN_EXTRA가 있으면 두 토큰 모두 200, 모르는 토큰 401, 토큰이 없으면 모두 401, 보내는 토큰을 바꿔도 이전 토큰으로 서명한 첨부 URL은 유효(EXTRA를 비우면 401) | test_agent_integration.py |
| 로그 | 접속 로그의 `sig=` 값 → `***`, 다른 주소는 그대로, uvicorn.access 로거에 필터가 붙어 있음 | test_agent_integration.py |
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
| 정리 명령 | 24시간 지난 중복 방지 키 삭제(지운 키는 새 요청으로 처리), 24시간 지나도록 검토 건에 안 붙은 첨부 삭제(최근 파일·붙은 파일은 남김, 지운 첨부로 요청하면 422), DB에 없는 파일은 1시간 지난 것만 삭제, 폴더 밖 경로 거부, `--dry-run`은 아무것도 지우지 않음 | test_maintenance.py |

### HTTP 연결 확인

실제 서버와 HTTP로 동작하는 가짜 Agent 서버를 따로 띄워서 확인했다. 결과는 다음과 같다.

- AI 심의(부적합 v1) → AI 추천 → 재심의(적합 v2)가 끝까지 동작했다.
- 작업 요청(`httpx`)과 완료 통지가 서버 사이에서 실제로 오갔다.
- Agent가 서명 URL로 첨부 파일을 내려받았다.
- 실제 uvicorn 접속 로그에 첨부 다운로드 주소가 `...&sig=*** HTTP/1.1" 401`처럼 서명이 가려져서 남았다.

### 아직 못 한 것

- **진짜 Agent와의 연동 확인**: Agent 서버가 준비되면 같은 시나리오를 다시 돌린다.

## 9. Agent 담당과 정한 것 (2026-11-27)

| 주제 | 정한 내용 | 반영 |
|---|---|---|
| 첨부 실패 코드 | 일시적 실패 `ATTACHMENT_DOWNLOAD_FAILED`(retryable=true), 파일 자체 문제 `INVALID_INPUT`(retryable=false) | 4장. 백엔드는 받은 값을 그대로 저장 |
| 같은 runId 재수신 | Agent는 다시 실행하지 않는다. 처음·진행 중 202, 이미 끝남 200(현재 상태), 완료 통지를 못 보냈으면 같은 결과를 다시 보냄 | 3장. 백엔드는 202·200을 모두 접수로 처리 |
| 토큰 교체 | 교체하는 동안 이전·새 토큰을 모두 받는다 | 7장 '서비스 토큰 교체'. `AGENT_TOKEN_EXTRA` |
| AI 추천 입력 | 최초 AI 심의 보고서를 `initialReport`로 보낸다 | 3장 |
| 서명 URL 로그 | 백엔드는 접속 로그에서 서명을 가리고, Agent는 `attachmentId`만 남긴다 | 7장 '서명 URL과 로그' |

- 설계서 v5.3 7장 실패 코드 표의 `AGENT_UNAVAILABLE` 설명("202가 아닌 응답")은 이 합의에 맞춰 "202·200이 아닌 응답"으로 고쳤다 (설계서 v5.3 수정본).

## 10. 정리 명령

오래된 중복 방지 키와 남는 첨부 파일을 지운다. 코드: `src/backend/app/maintenance.py`

```
cd src/backend
uv run python -m app.maintenance            # 지운다
uv run python -m app.maintenance --dry-run  # 지우지 않고 지울 개수만 본다
```

| 대상 | 지우는 기준 | 순서 |
|---|---|---|
| 중복 방지 키 (`idempotency_keys`) | 만든 지 24시간이 지남 | 한 번에 삭제 |
| 검토 건에 연결되지 않은 첨부 | 올린 지 24시간이 지나도록 검토 요청에 쓰이지 않음 | 첨부마다 DB 행 삭제 → 커밋 → 파일 삭제. 그 사이 검토 건에 붙었으면 건너뜀 |
| DB에 없는 파일 (첨부 폴더) | `attachments` 행이 없고, 바뀐 지 1시간이 지남 (올리는 중인 파일 보호) | 파일 삭제. 첨부 폴더 밖 경로는 지우지 않음 |

- 배포 서버에서는 하루 한 번 예약 실행한다 (cron·작업 스케줄러).
- 첨부 행을 먼저 지우므로, 그 파일 삭제가 실패해도 같은 실행의 'DB에 없는 파일' 정리에서 다시 지운다.
- 지운 키로 다시 요청하면 새 요청으로 처리된다. 지운 첨부로 검토를 요청하면 422(`attachmentIds[i]` INVALID)라 다시 올리면 된다.
- 기준: 설계서 v5.3 수정본 2장 '보관·삭제', 3장 DB 밖 데이터 정리, 부록 C #42·#43.
