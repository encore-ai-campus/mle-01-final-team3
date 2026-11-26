# Neo4j 그래프 스키마 설계서 — 초안

- 상태: 초안 v0.2 — 강사 지도사항 반영; 실제 청킹·구조화 데이터 대조 전
- 목적: 규정 그래프와 심의 절차 그래프의 초기 모델, 제출 필수 산출물 체크리스트, 실제 데이터로 확정할 사항을 정리한다.
- 적용 기준: 전달 브리프, docs/청킹_보완_필요.md, data/document_registry.csv

> 이 문서는 청킹 완료 후 바로 보완할 수 있도록 만든 작업 초안이다. 아래의 노드·관계 이름은 설계 제안이며, 실제 데이터에 없는 속성·관계·절차를 확정된 사실처럼 생성하지 않는다. 미확정으로 표시한 사항은 청킹 산출물 및 담당자 확인 후 확정한다.

## 1. 목표와 범위

두 개의 논리 그래프를 설계한다.

1. **Neo4j-규정 그래프**: 조항, 위반 유형, 광고 표현, 원료, 사례를 원문 근거와 연결한다.
2. **Neo4j-절차 그래프**: 심의 단계, 담당 역할, 조건, 결과와 단계 간 이동을 표현한다.

두 그래프 모두 원문 근거를 추적할 수 있어야 한다. 기본 근거 식별자는 청킹 결과의 document_id와 chunk_id이며, 문서 정보는 문서 레지스트리를 기준으로 연결한다.

이번 초안의 범위는 논리 스키마와 검증 기준이다. 논리 모델에는 Neo4j 설치 버전이 필요하지 않다. 실제 제약·인덱스 문법과 적재 쿼리를 작성할 때 Neo4j 버전과 청킹 산출물을 확인한다.

## 2. 현재 확인된 데이터와 제약

### 확인된 사항

- 전달 브리프는 입력 데이터 유형을 법령 API, 행정규칙 API, OCR/PDF, 심의 가이드 레코드, 위반사례 DB의 다섯 종류로 나눈다.
- 브리프는 법령의 조·항·호·목 구조 보존, 사례·가이드의 의미 단위 분할, 원문 위치 추적을 요구한다.
- data/document_registry.csv에는 파싱 문서 453개가 등록되어 있다. document_id, source_path, title, version, chunk_path를 포함한다.
- 레지스트리에는 기존 청크에서 사용한 ID가 보존되어 있다. 따라서 아래 예시의 DOC-000001은 형식 예시일 뿐이며, 실제 적재 시에는 레지스트리의 document_id를 그대로 사용해야 한다.
- 레지스트리에서 버전을 확인할 수 없는 행이 있다. 해당 버전은 메타데이터 담당자 확인 전까지 미확정으로 둔다.
- EDA 보고서는 식품원료의 대표 원료명이 고유하다고 해서 공식 기본키로 간주하면 안 된다고 지적한다. 원료 노드 키는 공식 식별자 여부를 확인하기 전까지 원료명만으로 확정하지 않는다.
- 새 백엔드 DOCX는 ERD·상태 전이 원본을 v0.4로 갱신한다. 이전 PDF와 흐름도에 있던 직접 재작성과 부적합 보고서 14일 삭제 규칙은 새 문서에서 철회되었으므로, 변경된 항목은 새 DOCX를 우선 기준으로 삼는다.
- 새 백엔드 문서는 심의 참조 엔터티를 8종으로 정리한다. 광고 게시물과 심의 판단은 백엔드 테이블에서 관리하고, 제품·업체·원재료·기능성 인정·법령 근거·행정처분 6종은 온톨로지가 관리한다.
- 새 문서에서 각 광고 검토 건의 보고서에 버전이 추가되었다. 최초 AI 심의는 v1, 성공한 RA_RECHECK마다 1씩 증가하며, 보고서는 버전별 원문과 판정을 보존한다.
- 백엔드 API 설계서 v5.0에는 MARKETING·LEGAL·ADMIN 역할, 광고 검토부터 AI 판정·법무 의견·게시 또는 후속 조치까지의 업무 상태 전이가 구체적으로 정의되어 있다. 첨부 흐름도와 멀티에이전트 메모가 AI 내부 실행 흐름을 보완한다.
- 멀티에이전트 메모에서는 supervisor가 stage에 따라 도구·경로를 선택하고, AI_SCREENING과 RA_RECHECK는 검색 후 판정, RA_SUGGEST는 추천 문구 생성만 수행한다. RA_RECHECK 전용 에이전트를 별도로 두지 않는다고 명시한다.
- 도메인 온톨로지 설계서는 Product, Company, Ingredient, FunctionalClaim, AllowedPhrase, Advertisement, ViolationType, ReviewDecision, LegalBasis, EnforcementAction 등을 후보 개념으로 제시한다. 다만 이 문서는 예시 데이터·규정·수치가 가상이라고 명시하므로 클래스·속성·관계는 초안 입력으로만 사용한다.
- API 설계서의 도메인 예시와 별표 1 위반 코드표는 실제 허용 코드와 백엔드 필드에 맞춰 검증해야 한다. 보고서 예시의 조문·사례 문구는 문서에서 가상 예시라고 밝힌 부분을 실데이터처럼 적재하지 않는다.

### 아직 근거 데이터로 확인되지 않은 사항

- 새 규격에 맞춘 structured_chunks.jsonl, chunk_schema.json, chunking_quality_log.jsonl 및 대표 샘플은 이 초안의 기준 자료에 포함되어 있지 않다.
- 브리프에는 위반사례 DB가 제시되어 있으나, 그래프에 적재할 최종 레코드 식별자와 중복·전량 적재 정책은 확정되지 않았다.
- 팀이 합의한 시스템 흐름도를 광고 심의 절차의 SOP 기준으로 사용한다. 상세 상태·API 필드와 흐름도 간 불일치는 최신 백엔드 DOCX v0.4를 기준으로 해석한다.
- 백엔드 API는 업무 엔터티·상태값을 정의하지만, 도메인 엔터티 중 어떤 것을 Neo4j에 실제 노드로 둘지는 아직 결정되지 않았다. 트랜잭션 원장과 지식 그래프의 책임을 중복시키지 않도록 CQ와 조회 요구로 확정한다.
- 멀티에이전트 메모는 선택된 검색 도구와 실행 경로를 로그로 남기도록 요구한다. 백엔드 API 명세에 이 로그의 저장 필드·콜백이 명시되어 있는지는 확인되지 않아 연동 계약을 맞춰야 한다.
- 표현·위반 유형·원료 간 관계는 실제 출처에서 확인된 내용만 그래프 사실로 만들며, 이름이 비슷하다는 이유로 자동 병합하지 않는다.

## 3. 공통 식별자와 근거 원칙

### 식별자

| 그래프 요소 | 권장 식별자 | 규칙 |
|---|---|---|
| 문서 | document_id | data/document_registry.csv 값 그대로 사용 |
| 청크·조항 | chunk_id | structured_chunks.jsonl 값 그대로 사용 |
| 사례 | chunk_id 또는 원본의 안정적인 레코드 ID | 실제 산출물에서 고유성과 지속성을 확인한 뒤 확정 |
| 표현·위반 유형·원료·절차 개념 | 공식 ID가 있으면 공식 ID, 없으면 네임스페이스가 포함된 내부 ID | 이름 단독 키 사용 여부는 미확정; 동의어와 동명이인 검토 필요 |
| 근거 주장 | evidence_id | 결정 후 source_chunk_id와 주장 식별자를 조합하거나 별도 발급 |

ID 예시의 구조는 다음과 같다. 값은 모두 예시이며 실제 ID를 대체하지 않는다.

~~~text
(document_id)  DOC-000001
(chunk_id)     DOC-000001:A008:P001:I001
(parent_id)    DOC-000001:A008:P001
~~~

**필수 규칙:** 적재 전 document_id가 레지스트리에 존재하는지 확인한다. 출처 청크를 참조하는 근거는 source_id = document_id, source_chunk_id = chunk_id로 일치시킨다. 조항·페이지·레코드 위치는 청크 필드와 출처 데이터로 역추적 가능해야 한다.

### 근거를 보존하는 방식 — 제안

도메인 관계를 만들 때 출처를 잃지 않도록 Evidence를 주장 단위로 둔다. Evidence는 하나 이상의 원문 청크를 인용하고, 어떤 주체와 객체 사이의 어떤 주장을 지지하는지 연결한다.

~~~mermaid
graph LR
  S[도메인 주체] -->|SUBJECT| E[Evidence]
  E -->|OBJECT| O[도메인 객체]
  E -->|CITES| C[Chunk]
  C -->|BELONGS_TO| D[Document]
~~~

이 구조는 하나의 사실을 여러 문서가 뒷받침하거나, 같은 두 개념 사이의 관계에 서로 다른 근거가 있는 경우를 보존하기 위한 제안이다. 초안에서는 `주체 → Evidence(predicate) → 목적어`를 주장 원장으로 둔다. 실제 조회 성능을 위해 직접 엣지를 추가하는 경우에도 Evidence의 출처 연결을 유지하고, 직접 엣지가 원문 사실인지 파생 결과인지 구분한다. 두 표현을 독립적으로 수정해 서로 다른 사실이 되는 것을 막는다. 근거 없는 추론을 법적 사실로 저장하지 않는다.

## 4. 규정 그래프 초안

### 노드 라벨과 핵심 속성

Chunk는 원문을 보존하는 공통 라벨로 두고, 의미에 따라 보조 라벨을 붙이는 방식을 제안한다. 같은 실제 청크를 근거와 원문 보존 목적으로 중복 노드화하지 않는다.

| 라벨 | 역할 | 초안 속성 | 상태 |
|---|---|---|---|
| Document | 원문 문서와 레지스트리 연결 | document_id, title, version, source_path | 필드 출처 확인됨; 버전 일부 미확정 |
| Chunk | 원문 청크 및 모든 근거의 기준 노드 | chunk_id, document_id, chunk_type, text, article, paragraph, item, subitem, source_page, source_span | 청킹 결과 확인 후 확정 |
| Provision | 법령·고시의 조항, 표, 부칙 등 규정 단위 | 청크 식별자와 위치 필드 사용 | 청크 타입과 필드 매핑 미확정 |
| LegalBasis | 법령·고시 등 법적 근거 개념 | legal_basis_id, 명칭, 시행일, 원문 근거 | 백엔드 v0.4의 온톨로지 관리 엔터티; 실제 원천 필드·ID 확인 필요 |
| ReviewCase | 위반사례 또는 심의 사례 | 출처 레코드 ID, 사건에 실제 존재하는 속성 | 원본 키·필드 매핑 미확정 |
| Expression | 사례에서 확인된 광고·표현 문구 | 정규화 문구, 원문 문구(필요 시 분리) | 표현 단위와 중복 정규화 미확정 |
| ViolationType | 보고서의 표준 위반 코드·유형 | violation_code, 명칭, 코드표 버전 | API 부록 D에 코드표 있음; 청크 근거·최신성 대조 필요 |
| Ingredient | 원료 데이터의 원료 개념 | 공식 원료 키, 표준명, 출처별 명칭 | 공식 키와 동의어 정책 미확정 |
| Product | 광고 대상 제품 | PRDLST_REPORT_NO, product_category, 법정 품목 유형 | 온톨로지 초안과 백엔드 설계 후보; 실제 필드 대조 필요 |
| Company | 제품 제조·취급 업체 | LCNS_NO, 업소명, 인허가 정보 | 온톨로지·API 설계에서 후보 중심키 확인; 권한·개인정보 범위 확인 필요 |
| FunctionalClaim | 기능성 인정 사실 | 내부 ID, 인정번호, 기능성 원문, 적용 기간 | 후보 개념; 인정번호는 중복 가능성이 있어 단독 기본키로 사용하지 않음 |
| AllowedPhrase | 조건에 따라 허용되는 문구 | phrase_id, 원문, 적용 조건, 유효 기간 | 후보 개념; 고시·인정 자료에서 출처와 단위 확인 필요 |
| Advertisement / Review | 제출된 광고 및 검토 건 | review_id, title, product_category, text | 백엔드 테이블에서 관리; 그래프 노드화는 조회 요구에 따라 결정 |
| ReviewDecision / Report | AI 심의·재심의 결과 | run_id, review_id, version, stage, decision, reviewed_text, findings | 백엔드 reports 테이블; 버전별 보고서와 이전 버전 연결 |
| EnforcementAction | 행정 처분·후속 조치 | 원본 처분 키, 처분 유형·일자 | 후보 개념; 원본 식별자·개인정보 범위 확인 필요 |
| Evidence | 하나의 출처 기반 주장을 표현하는 근거 노드 | evidence_id, predicate, source_id, source_chunk_id, source_page, source_span, polarity, conditions | 청크 산출물과 주장 구조 확인 후 확정 |

Provision은 Chunk의 보조 라벨로 표현하는 안을 권장한다. 사례 청크도 Chunk와 ReviewCase를 함께 붙일 수 있으나, 사례 레코드의 ID와 청크 ID가 같다는 점이 확인된 뒤 적용한다.

최신 백엔드 DOCX는 심의 참조 엔터티 8종 가운데 Advertisement와 ReviewDecision을 백엔드 테이블에서 관리하고, Product·Company·Ingredient·FunctionalClaim·LegalBasis·EnforcementAction 6종은 온톨로지가 관리한다고 정리한다. 따라서 이 여섯 노드는 Neo4j 온톨로지의 핵심 후보이고, Advertisement/ReviewDecision은 백엔드 ID를 참조하는 방식을 기본으로 한다. 온톨로지 초안의 AllowedPhrase·ViolationType 등 추가 개념은 API의 기준 집합과 구별해, 실제 CQ·검색 경로와 청킹 자료가 뒷받침할 때 별도 노드로 확정한다. Review/Run/Report/LegalSubmission은 트랜잭션 이력이므로 Neo4j에 복제하는 범위는 GraphRAG 조회 요구에 따라 결정한다.

### 관계 초안

| 시작 노드 | 관계 | 도착 노드 | 의미·주의 |
|---|---|---|---|
| Document | HAS_CHUNK | Chunk | 문서의 청크 |
| 부모 Chunk | CONTAINS | 자식 Chunk | parent_id 계층을 그래프 관계로 표현 |
| ReviewCase | HAS_EXPRESSION | Expression | 사례에서 확인된 표현. 광고 문구의 원문 근거 필수 |
| ReviewCase | CLASSIFIED_AS | ViolationType | 출처에 명시되거나 승인된 분류에 한정 |
| ViolationType | GROUNDED_IN | Provision | 해당 유형의 규정 근거가 원문으로 확인된 경우 |
| Ingredient | REGULATED_BY | Provision | 규정이 해당 원료에 실제 적용됨을 근거로 확인한 경우 |
| 도메인 노드 | SUBJECT / OBJECT | Evidence | 근거가 지지하는 주장 연결 |
| Evidence | CITES | Chunk | source_chunk_id로 원문 청크 참조 |

관계/주장의 속성은 우선 Evidence에 둔다. 최소 `predicate`와 출처 식별값을 보존하며, 원문에 명시된 경우에만 적용 조건·예외·유효 기간 등을 둔다. 관계 엣지 속성으로 둘 항목이 생기면 원문 근거와 변경 이력 필요성을 검토해 별도로 확정한다. 구체적인 속성과 자료형은 청크 및 실제 트리플을 대조한 뒤 정한다.

관계 이름과 방향은 제안이다. 법령에 단순히 단어가 함께 나온다는 이유만으로 REGULATED_BY, GROUNDED_IN, CLASSIFIED_AS를 생성하지 않는다. 각 관계는 원문 인용 또는 승인된 분류 데이터가 있어야 한다.

### 온톨로지–Neo4j 매핑 및 실제 S-P-O 근거

지도 PDF의 제출 기준은 온톨로지의 클래스·관계·속성을 Neo4j에 매핑하고, 가상 트리플을 실제 법령 근거로 교체해 출처까지 연결하는 것이다. 아래 표는 청킹 완료 후 실제 데이터로 채운다. 현재는 후보와 검증 기준만 둔다.

| 온톨로지 항목 | Neo4j 라벨/관계 | 필수 식별키·속성 | 실제 청크 근거 | 결정 상태 |
|---|---|---|---|---|
| 클래스별 매핑 | 해당 노드 라벨 | 공식 키 또는 내부 ID, 핵심 속성 | 해당 시 대표 source_chunk_id | 청킹 자료 대조 후 작성 |
| 관계별 매핑 | 관계 유형 또는 Evidence.predicate | 방향, 관계 속성, 유효기간·조건(원문에 있을 때) | 관계를 직접 뒷받침하는 청크 | 청킹 자료 대조 후 작성 |
| 법령 S-P-O | 주어–Evidence–목적어 | subject_id, predicate, object_id | document_id, source_chunk_id, source_span, 원문 인용 | 실제 법령 샘플로 작성 |
| 부정·예외·조건 | Evidence/관계의 한정 속성 | polarity, condition, exception, valid_from/to 등 | 해당 조건을 말하는 원문 청크 | 원문에서 확인된 경우에만 작성 |

S-P-O는 표면상 관계만 옮기지 말고 적용 대상, 조건, 예외, 시행 시점이 원문에 있으면 함께 보존한다. 관계마다 근거 청크를 연결하고, 인용 원문과 청크가 같은 명제를 뒷받침하는지 검토한다. 식품 광고의 위법 여부나 인정 가능성을 단어 유사도만으로 확정하지 않는다.

### 규정 그래프 개념도

~~~mermaid
graph TD
  D[Document] -->|HAS_CHUNK| C[Chunk / Provision]
  C -->|CONTAINS| C2[하위 조항 Chunk]
  RC[ReviewCase] -->|HAS_EXPRESSION| EX[Expression]
  RC -->|CLASSIFIED_AS| VT[ViolationType]
  VT -->|GROUNDED_IN| P[Provision]
  ING[Ingredient] -->|REGULATED_BY| P
  EV[Evidence] -->|SUBJECT / OBJECT| RC
  EV -->|CITES| C
~~~

## 5. 심의 절차 그래프 초안

팀이 합의한 시스템 흐름도를 업무 절차의 SOP 기준으로 삼고, 최신 백엔드 API DOCX의 ERD·상태 전이 v0.4로 세부 상태와 데이터 계약을 보완한다. 두 자료가 충돌하면 직접 재작성, 보고서 보존, 버전 이력 등 최신 DOCX에서 갱신된 규칙을 우선한다. 멀티에이전트 메모는 AI 내부 경로를 보완한다. 법무 검토는 법정 심의와 구별하고, AI의 적합·부적합 판정과 마케팅의 게시 판단을 별도 단계로 유지한다.

### 문서에서 확인한 절차 규칙

| 단계 / 분기 | 담당·실행자 | 조건과 결과 |
|---|---|---|
| 광고 검토 요청 | MARKETING 작성자 | 광고 문구와 제품 분류를 제출하면 새 Review와 AI_SCREENING 실행을 만든다. |
| AI 심의·재심의 | Supervisor → 검색 도구 → 판정 모델 | Supervisor가 벡터 검색, GraphRAG 또는 둘 다를 고른다. AI 결과는 SUITABLE 또는 UNSUITABLE이다. |
| 적합 보고서 | MARKETING 작성자 | 법무 검토 요청 또는 요청 안 함(ENDED)을 선택한다. 법무 검토 요청은 적합 보고서에만 허용된다. |
| 법무 검토 배정 | LEGAL | 먼저 검토 시작을 누른 담당자가 배정된다. 담당자는 검토 의견만 작성·전송하며 적합·부적합을 판정하지 않는다. |
| 법무 의견 후 결정 | MARKETING 작성자 | 게시 가능이면 PUBLISHED, 수정 필요면 AI 추천 요청 또는 심의 취소를 선택한다. 문구를 직접 고치는 경우 기존 검토 건을 취소한 뒤 새 검토 요청을 만든다. |
| 부적합 보고서 후속 조치 | MARKETING 작성자 | AI 추천 요청 또는 심의 취소 중 선택한다. 직접 재작성은 제공하지 않으며, 문구를 직접 고치려면 취소 후 새 검토 건을 제출한다. |
| 추천 문구 생성 | RA_SUGGEST | AI가 추천 문구만 생성한다. 자동 재심의하지 않는다. 결과는 확인 대기 상태가 되고, 사용자는 닫기 또는 재심의를 선택한다. 추천 요청 횟수 제한은 없다. |
| 추천 문구 재심의 | RA_RECHECK | 작성자가 확인한 문구를 같은 Supervisor → 검색 → 판정 모델 흐름으로 보낸다. 같은 Review에 새 Run을 추가하고, 성공하면 새 Report 버전을 만든다. 별도 RA_RECHECK 에이전트는 만들지 않는다. |
| 직접 수정 후 새 검토 | MARKETING 작성자 | 현재 Review를 CANCELED로 끝낸 뒤 새 검토 요청으로 독립된 Review를 만든다. v0.4에는 두 Review를 잇는 원본 ID 필드가 정의되어 있지 않으므로 그래프 링크를 만들지 않는다. |
| 실행 실패·재시도 | 실패한 단계의 작성자 | Run은 QUEUED → RUNNING → SUCCEEDED 또는 FAILED로 진행한다. 시간 초과 기준은 접수 후 180초이며, 실패 실행별 재시도는 최대 2회다. 재시도는 새 Run이다. |
| 끝 처리 | MARKETING 작성자 | ENDED(법무 미요청), PUBLISHED(게시 완료), CANCELED(심의 취소). 종료 후에는 후속 처리를 막는다. |
| 보고서 버전 | 백엔드 | 최초 AI_SCREENING 보고서는 v1, 성공한 RA_RECHECK마다 같은 Review의 보고서 버전이 1씩 증가한다. 추천 생성·닫기·실패·재시도는 버전을 올리지 않는다. |
| 보고서 보존 | 백엔드 | v0.4에서는 적합·부적합 보고서와 법무 검토 의견을 삭제하지 않는다. |

상태 코드는 API 계약을 따른다. Run의 stage는 AI_SCREENING, RA_SUGGEST, RA_RECHECK이며 Run status는 QUEUED, RUNNING, SUCCEEDED, FAILED다. Report의 decision은 SUITABLE 또는 UNSUITABLE이다. 각 Report에는 review_id별 version과 해당 버전의 reviewed_text가 있다. previousReport는 같은 Review에서 version-1인 Report를 가리키며, v1에는 이전 보고서가 없다. LegalSubmission은 PENDING → IN_REVIEW → OPINION_SENT로 관리한다. NOT_SENT는 별도 요청이 없는 적격 건의 계산 표시값이며, 법무 요청 대상이 아닌 부적합 건에는 legalStatus가 없다. Suggestion은 PENDING → RECHECKED 또는 DISMISSED로 관리한다. Review의 최종 업무 상태는 별도 상태 컬럼에 저장하지 않고 실행·보고서·법무 전송·끝 처리 이력에서 계산한다고 명세되어 있으므로, 그래프에 별도의 현재 상태를 중복 저장하지 않는다.

### 노드 모델

절차 그래프는 **절차 정의**와 **업무 실행 이력**을 구분한다. 백엔드가 이미 소유하는 업무 레코드와 Neo4j를 이중 원장으로 만들지 않는다. 필요하면 API ID를 그래프에서 참조하고, 업무 원장 자체가 어느 시스템인지 확정하기 전까지는 Neo4j가 해당 상태를 권위 있게 소유한다고 가정하지 않는다.

| 라벨 | 역할 | ID·속성 후보 | 출처 / 상태 |
|---|---|---|---|
| ReviewProcess | 광고 심의 업무 절차 정의 | process_id, name, version | 팀 합의 시스템 흐름도를 SOP 기준으로 사용; API DOCX v0.4가 세부 상태를 보완 |
| ProcessStep | 요청, 심의, 법무 의견, 추천 확인 등 절차 단계 정의 | step_id, name, sequence | 단계명·순서는 API/흐름도에서 확인 |
| Condition | 분기를 만드는 판정·사용자 선택·실행 결과 | condition_id, condition_type, value | 조건은 아래 전이표에서 확인; ID·저장법은 제안 |
| ActorRole | 업무상 역할 | role_code, name | MARKETING, LEGAL, ADMIN |
| Participant | 실제 요청자·담당자 참조 | user_id, role_code | API userId를 가리키는 가명 참조 후보; 개인정보·접근정책 합의 후 사용 |
| AgentComponent | AI 실행 구성요소 | component_id, component_type, name | Supervisor, 검색 도구, 판정 모델, 추천 문구 생성기 |
| Review | 광고 검토 건 | review_id, author_id, product_category, created_at, close_type, closed_at | 백엔드 reviews 모델 |
| ReviewRun | AI 심의·추천·재심의 1회 실행 | run_id, review_id, stage, status, attempt, timestamps | 백엔드 review_runs 모델 |
| Report | 성공한 판정 결과의 버전별 이력 | run_id, review_id, version, stage, decision, reviewed_text, summary, findings | 백엔드 reports 모델; (review_id, version) 고유; RA_SUGGEST는 Report를 만들지 않음 |
| LegalSubmission | 특정 적합 보고서에 대한 법무 검토 요청 | submission_id, report_run_id, status, sender_id, reviewer_id, sent_at, decided_at, reason | 백엔드 legal_submissions 모델 |
| Suggestion | AI가 만든 확인 대기 문구 | run_id, review_id, text, rationale, status | review_runs.suggestion; PENDING/RECHECKED/DISMISSED |
| Evidence | 단계·판정·관계를 뒷받침하는 출처 | evidence_id, source_id, source_chunk_id, source_page, source_span | 청크 산출물 확인 후 확정 |

Review, ReviewRun, Report, LegalSubmission, Suggestion은 API가 이미 정의한 실행·업무 엔터티다. 이를 Neo4j에 노드로 둘지는 GraphRAG/조회 요구가 있는지에 따라 결정하고, 처음에는 백엔드 ID와 관계를 연결하는 참조 모델을 권장한다. ActorRole은 역할값만 표현한다. ADMIN은 사용자·권한·담당 건 관리 역할이며 광고 심의 판정 흐름의 행위자로 넣지 않는다. 개별 담당자 참조가 꼭 필요하면 Participant에는 API userId만 쓰고 이름·이메일은 복제하지 않는다.

### 관계 모델

| 시작 노드 | 관계 | 도착 노드 | 의미 |
|---|---|---|---|
| ReviewProcess | HAS_STEP | ProcessStep | 절차에 정의된 단계 |
| ProcessStep | NEXT_STEP | ProcessStep | 순차 단계 |
| ProcessStep | BRANCHES_ON | Condition | 조건 평가 |
| Condition | LEADS_TO | ProcessStep | 조건값에 따른 다음 단계; condition value는 실제 상태코드·선택값 사용 |
| ProcessStep | OWNED_BY | ActorRole | 업무상 책임 역할 |
| ProcessStep | EXECUTED_BY | AgentComponent | AI가 담당하는 단계 |
| Review | CREATED_BY | Participant | 작성자 식별이 필요할 때 API userId만 참조; 이름·이메일 복제 금지 |
| Review | HAS_RUN | ReviewRun | 한 검토 건의 실행 이력 |
| ReviewRun | PRODUCED | Report | 판정 실행 결과; RA_SUGGEST에는 연결하지 않음 |
| ReviewRun | GENERATED | Suggestion | 추천 문구 실행 결과 |
| Review | HAS_LEGAL_SUBMISSION | LegalSubmission | 같은 광고 검토 건에서 발생한 법무 요청 |
| LegalSubmission | REQUESTED_BY / ASSIGNED_TO | Participant | API sender_id / reviewer_id를 참조; 사용자 속성 복제는 금지 |
| Report | PREVIOUS_VERSION | Report | 현재 버전에서 같은 Review의 직전 보고서(version-1)를 가리킴; v1은 연결 없음 |
| LegalSubmission | FOR_REPORT | Report | report_run_id로 요청 당시의 특정 적합 보고서 버전을 고정 |
| Evidence | CITES | Chunk | 절차·판정 관계의 원문 근거 |

### 업무 조건과 전이

실제 전이의 조건은 다음처럼 정의한다. 별도의 상태 전이 노드를 만들지 않고 ProcessStep과 Condition을 사용하거나, 런타임 이벤트만 저장하고 단계 정의 그래프를 두지 않는 선택은 조회 요구를 확인한 뒤 확정한다.

| 현재 단계 / 조건 | 담당 | 전이 또는 결과 |
|---|---|---|
| 검토 요청 | 마케팅 작성자 | 새 Review와 AI_SCREENING Run 생성 |
| AI 판정 = SUITABLE | 마케팅 작성자 | 법무 요청이면 LegalSubmission 생성; 요청하지 않으면 ENDED |
| 법무 검토 요청 상태 = PENDING | 먼저 시작 버튼을 누른 법무 담당자 | IN_REVIEW로 전이 및 담당자 지정 |
| 법무 검토 중 | 지정된 법무 담당자 | 의견 전송 시 OPINION_SENT; 의견은 적합·부적합 판정이 아님 |
| 의견 = 게시 가능 | 마케팅 작성자 | PUBLISHED |
| 의견 = 수정 필요 | 마케팅 작성자 | RA_SUGGEST 또는 CANCELED; 직접 고칠 경우 취소 후 새 Review 제출 |
| AI 판정 = UNSUITABLE | 마케팅 작성자 | RA_SUGGEST 또는 CANCELED; 직접 고칠 경우 취소 후 새 Review 제출 |
| Suggestion = PENDING, 재심의 선택 | 마케팅 작성자 | Suggestion=RECHECKED, 같은 Review에 RA_RECHECK Run 추가 |
| Suggestion = PENDING, 닫기 선택 | 마케팅 작성자 | Suggestion=DISMISSED; 직전 Report 유지 |
| RA_RECHECK 성공 | 백엔드 | 새 Report 생성, 같은 Review 내 version이 1 증가; 직전 Report 보존 |
| RA_SUGGEST·닫기·실패·재시도 | 백엔드 | 보고서 버전은 바뀌지 않음 |
| 취소 후 새 검토 | 마케팅 작성자 | 새 독립 Review 생성; v0.4에는 원본 Review를 참조하는 필드가 정의되어 있지 않음 |
| Run 실패, 재시도 가능 | 해당 단계의 작성자 | 새 Run을 만들고 실패 Run은 보존; 실행별 최대 2회 재시도 |

AI 역할은 사람의 MARKETING/LEGAL 권한과 별도로 모델링한다. 멀티에이전트 메모에 따르면 Supervisor가 검색 도구를 선택하고 판정 모델에 검색 근거와 문구를 전달한다. 추천 문구 생성은 RA_SUGGEST에서만 수행한다. 도구 선택·실행 경로 로그를 그래프에 둘지는 백엔드/API 로그 계약과 조정한 뒤 확정한다.

### 절차 그래프 개념도

~~~mermaid
graph TD
  M[MARKETING] -->|요청| R[Review]
  R -->|HAS_RUN| A[ReviewRun: AI_SCREENING]
  A -->|Supervisor가 경로 선택| T[검색 도구]
  T --> V[판정 모델]
  V -->|SUITABLE| L{법무 검토 요청?}
  L -->|예| LS[LegalSubmission]
  LS -->|의견 전송| LM[MARKETING 후속 결정]
  LM -->|게시 가능| PUB[PUBLISHED]
  LM -->|수정 필요| S[RA_SUGGEST]
  V -->|UNSUITABLE| F{후속 조치 선택}
  F -->|추천| S
  S --> SG[Suggestion 확인 대기]
  SG -->|재심의| RC[RA_RECHECK 새 Run]
  SG -->|닫기| DIS[DISMISSED]
  F -->|취소| CAN[CANCELED]
  CAN -.->|직접 수정 후 새 요청| R2[독립된 새 Review]
  RC -->|성공 시 version +1| RP[새 버전 Report]
  E[Evidence] -->|CITES| C[근거 Chunk]
~~~

## 6. 키·제약 및 적재 원칙 — 제안

- Document.document_id와 Chunk.chunk_id는 유일해야 한다.
- Chunk.document_id는 레지스트리에 있는 문서를 가리켜야 한다.
- Chunk.parent_id가 값이면 같은 문서에 존재하는 부모 chunk_id를 가리켜야 한다. 최상위는 null이다.
- Provision의 식별자는 원문 조항 위치를 포함한 chunk_id로 삼는다. 조 번호만으로 노드를 식별하지 않는다. 서로 다른 문서·버전의 제8조가 충돌할 수 있다.
- 사례의 고유 키는 원본에서 제공하는 안정적 레코드 ID를 우선한다. 행 번호는 원본 정렬에 따라 바뀔 수 있어 키로 채택하지 않는다.
- 원료·위반 유형·표현·역할의 고유성은 이름만으로 판단하지 않는다. 공식 ID, 분류체계, 동의어·중복 처리 규칙을 확인한다.
- 원문 텍스트와 출처 표기는 정규화된 검색용 명칭과 분리해 원문을 보존한다.
- 출처가 페이지 단위인 문서는 source_page, 조항·문구 단위인 문서는 source_span을 채워 근거를 역추적한다. 해당 위치 정보가 없는 경우 임의로 만들지 않는다.
- 여러 문서·청크가 같은 관계를 뒷받침할 수 있으므로 근거를 단일 출처 문자열로 덮어쓰지 않는다.
- Product의 `PRDLST_REPORT_NO`를 상품 카탈로그 원본 ID 후보로 사용하되, 실제 카탈로그에서 null·중복 여부를 확인한 뒤 고유 제약을 건다. Ingredient는 별도 원본 식별자를 확인하기 전까지 상품 ID나 원료명으로 키를 추정하지 않는다.
- `Evidence`는 하나의 주장(S-P-O)을 표현하고 `predicate`와 원문 출처를 보존한다. 여러 근거 청크가 같은 주장을 지지하면 Evidence–CITES–Chunk를 여러 개 연결한다. 동일 출처·동일 주장 중복 정책은 적재 전에 정한다.

### 제약·인덱스 및 Cypher 설계 초안

아래 구문은 **Neo4j 5.x 계열을 가정한 제출용 초안**이며 실행 검증된 DDL이 아니다. 실제 설치 버전과 최종 라벨·ID 필드가 확정되면 버전에 맞춰 검증한다. 유일성 제약은 최종적으로 부여된 안정 키에만 적용한다.

```cypher
// 안정적인 식별키가 확정된 노드에만 적용한다.
CREATE CONSTRAINT document_id_unique IF NOT EXISTS
FOR (n:Document) REQUIRE n.document_id IS UNIQUE;

CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
FOR (n:Chunk) REQUIRE n.chunk_id IS UNIQUE;

CREATE CONSTRAINT product_report_no_unique IF NOT EXISTS
FOR (n:Product) REQUIRE n.PRDLST_REPORT_NO IS UNIQUE;

CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS
FOR (n:Evidence) REQUIRE n.evidence_id IS UNIQUE;

// 조회 패턴이 확정된 뒤 필요한 검색 인덱스만 추가한다.
CREATE INDEX provision_location IF NOT EXISTS
FOR (n:Provision) ON (n.document_id, n.article, n.paragraph, n.item, n.subitem);

CREATE FULLTEXT INDEX chunk_text_search IF NOT EXISTS
FOR (n:Chunk) ON EACH [n.text];
```

**인덱스 선택 근거를 함께 제출한다:** 고유 제약은 MERGE·중복 방지와 식별 조회에, 복합 위치 인덱스는 문서 내 조항 탐색에, 전문 인덱스는 청크 본문 검색에 사용한다. 예상 조회 패턴이 없거나 해당 속성이 최종 스키마에 없으면 인덱스를 만들지 않는다. `CREATE` 결과와 실제 DB 버전에서의 실행 여부를 제출서에 기록한다.

### 멀티홉 Cypher와 활용 검증 항목

멀티홉 쿼리는 아래 시나리오를 목표로 하되, `[실제 관계]`는 온톨로지와 청킹 근거를 확인한 뒤 이름·방향을 채운다. 근거 없는 관계를 쿼리 경로로 고정하지 않는다.

| 탐색 구간 | 확인할 연결 | 필요한 근거 |
|---|---|---|
| 광고 → 표현 | 제출 문구에서 추출된 실제 표현 | 광고/사례 원문 또는 입력 데이터 |
| 표현 → 위반 유형 | 표현과 위반 유형을 연결하는 분류·판단 | 사례·가이드 또는 명시된 분류 근거 |
| 상품 → 원재료 | 상품 카탈로그에 명시된 원재료 | 안정 상품 ID와 원본 성분 필드 |
| 원재료 → 기능성 인정 | 원료별 인정 정보 및 적용 조건 | 인정 데이터의 식별자·조건·유효기간 |
| 위반 유형 → 법령 조항 | 위반 유형에 적용되는 조항 | 실제 법령 S-P-O와 source_chunk_id |
| 법령·사례 → Evidence → Chunk | 결론 경로의 모든 주장 | 각 주장에 대한 원문 인용·위치 |

최종 쿼리는 최소 다음을 반환하도록 한다: 입력 광고/상품 ID, 연결된 표현·원재료·인정 정보·위반 유형·법령 조항, 경로에 포함된 각 Evidence의 source_id/source_chunk_id/source_span, 문서 버전·시행일(데이터에 있을 때), 검증되지 않은 구간 표시. 결과가 부분 경로만 찾았을 때 전체 결론처럼 표현하지 않는다.

아래는 Evidence 중심의 **쿼리 골격**이다. `$predicate_*` 값은 실제 S-P-O 매핑에서 확인한 술어로 대체해야 한다. 데이터 적재 전에는 관계가 존재한다고 가정하거나 실행 결과를 사실로 해석하지 않는다.

```cypher
MATCH (r:Review {review_id: $review_id})
MATCH (r)-[:SUBJECT]->(e0:Evidence)-[:OBJECT]->(ex:Expression)
WHERE e0.predicate = $predicate_review_expression
MATCH (r)-[:SUBJECT]->(e1:Evidence)-[:OBJECT]->(p:Product)
WHERE e1.predicate = $predicate_review_product
MATCH (p)-[:SUBJECT]->(e2:Evidence)-[:OBJECT]->(i:Ingredient)
WHERE e2.predicate = $predicate_product_ingredient
MATCH (i)-[:SUBJECT]->(e3:Evidence)-[:OBJECT]->(fc:FunctionalClaim)
WHERE e3.predicate = $predicate_ingredient_claim
MATCH (ex)-[:SUBJECT]->(e4:Evidence)-[:OBJECT]->(vt:ViolationType)
WHERE e4.predicate = $predicate_expression_violation
MATCH (vt)-[:SUBJECT]->(e5:Evidence)-[:OBJECT]->(prov:Provision)
WHERE e5.predicate = $predicate_violation_provision
MATCH (e0)-[:CITES]->(c0:Chunk)
MATCH (e1)-[:CITES]->(c1:Chunk)
MATCH (e2)-[:CITES]->(c2:Chunk)
MATCH (e3)-[:CITES]->(c3:Chunk)
MATCH (e4)-[:CITES]->(c4:Chunk)
MATCH (e5)-[:CITES]->(c5:Chunk)
RETURN r, ex, p, i, fc, vt, prov,
       collect(DISTINCT {
         predicate: e0.predicate, source_id: c0.document_id,
         source_chunk_id: c0.chunk_id, source_span: c0.source_span
       }) + collect(DISTINCT {
         predicate: e1.predicate, source_id: c1.document_id,
         source_chunk_id: c1.chunk_id, source_span: c1.source_span
       }) + collect(DISTINCT {
         predicate: e2.predicate, source_id: c2.document_id,
         source_chunk_id: c2.chunk_id, source_span: c2.source_span
       }) + collect(DISTINCT {
         predicate: e3.predicate, source_id: c3.document_id,
         source_chunk_id: c3.chunk_id, source_span: c3.source_span
       }) + collect(DISTINCT {
         predicate: e4.predicate, source_id: c4.document_id,
         source_chunk_id: c4.chunk_id, source_span: c4.source_span
       }) + collect(DISTINCT {
         predicate: e5.predicate, source_id: c5.document_id,
         source_chunk_id: c5.chunk_id, source_span: c5.source_span
       }) AS evidence;
```

이 골격의 노드 연결 및 술어는 논리 시나리오 예시일 뿐이며, 실제 매핑표와 청킹 자료에 없는 연결은 삭제하거나 보류한다. `FunctionalClaim` 연결이 원료가 아니라 제품에 귀속되는 데이터라면 해당 구간도 실제 모델에 맞게 바꾼다. 최종 제출본에는 인정 가능성의 근거·조건·유효기간을 포함하고, 경로 부재와 주장 출처 부재를 각각 검증하는 질의를 둔다.

**활용 판단:** 그래프 추론은 심의 담당자의 근거 탐색과 법무 검토 준비를 지원하는 후보 경로로 평가한다. 실제 적용 가능성, 예외, 시행 시점, 광고 문맥을 담당자가 원문으로 확인해야 하며, 그래프 경로만으로 적합·부적합이나 법률 의견을 자동 확정하지 않는다. 대표 질의별 기대 근거, 누락·오탐 사례, 담당자 검토 결과를 기록한 뒤 사용 범위를 정한다.

## 7. 청킹 완료 후 갱신할 항목

| 확인 항목 | 현재 상태 | 청킹 완료 후 할 일 |
|---|---|---|
| 레지스트리와 청크의 document_id 일치 | 레지스트리 존재; 최종 청크 대조 전 | 모든 ID를 CSV와 대조하고 미등록 ID를 해결 |
| 청크 ID·부모 계층 | 전달 규칙 제시됨; 새 산출물 미확인 | chunk_id 유일성, parent_id 존재·동일 문서 소속 확인 |
| chunk_type ↔ 그래프 라벨 | 허용 타입 정의됨; 실제 타입별 수량 미확인 | 각 타입을 Chunk·Provision·ReviewCase 등에 매핑 |
| 조·항·호·목 필드 | 전달 규칙 제시됨; 누락·OCR 오인식 미확인 | 법령 대표 샘플을 원문과 대조하고 위치 속성 확정 |
| 사례 및 위반 유형 | 브리프에 데이터 종류 기재; 실제 ID·분류값 미확인 | 레코드 키, 표현·위반 필드, 분류 출처와 중복 규칙 결정 |
| 원료 식별자 | EDA에서 명칭만 기본키로 삼지 말라는 주의 확인 | 공식 원료 코드 유무와 동의어·개별 인정 원료 연결 검증 |
| 절차 단계·담당·조건 | 팀 합의 시스템 흐름도를 SOP 기준으로 사용; API DOCX v0.4가 세부 상태를 보완 | 흐름도와 API 간 불일치를 확인하고, 청킹 청크 ID와 원문 위치를 연결 |
| 역할·AI 단계 | API/멀티에이전트 메모에서 MARKETING, LEGAL 및 stage 흐름 확인 | 사람 역할과 AgentComponent를 분리; 검색 선택 로그의 백엔드 계약 확인 |
| 온톨로지·API 엔터티 범위 | 백엔드 v0.4는 참조 엔터티 8종을 구분: 백엔드 관리 2종, 온톨로지 관리 6종; 온톨로지 초안의 추가 후보도 있음 | 실제 CQ·검색 경로 기준으로 그래프 노드와 백엔드 참조 엔터티를 합의 |
| 온톨로지–Neo4j 매핑·실제 S-P-O | 설계 후보만 있음; 실제 청크 기반 트리플 없음 | 클래스·관계·속성 매핑표를 채우고 실제 법령 청크와 출처 매핑 작성 |
| 노드/엣지 속성, 식별키, 제약·인덱스 | 제안 수준; Neo4j 설치 버전 및 실제 조회 패턴 미확인 | 확정된 식별키만 제약 적용; 각 인덱스의 조회 목적·실행 버전 기록 |
| Cypher 스키마 생성문 | Neo4j 5.x 가정 초안 추가; DB 실행 검증 전 | 팀 Neo4j 버전에서 DDL 실행 확인 후 제출용 구문 확정 |
| 광고 심의 멀티홉 질의 | 경로 후보와 파라미터 쿼리 골격 추가; 술어·근거 미확정 | 상품·원재료·인정·위반 유형·법령 경로를 실제 S-P-O와 evidence로 채우고 대표 질의 검증 |
| 광고·법무 활용 가능성 | 원문근거 탐색 지원으로 제한하는 원칙만 정리 | 대표 질의 결과를 심의/법무 담당자가 검토하고 사용 가능 범위·오탐·미탐을 기록 |
| Review/Run/Report 중복 적재 | 백엔드가 실행·판정 기록을 소유하는 것으로 명세 | Neo4j가 원장인지 조회용 참조 그래프인지 결정하고 중복 원장 방지 |
| 출처 근거 모델 | source 필드 요구 정의됨; 적재 형태 미확정 | Evidence 노드와 직접 관계 속성 방식 중 하나를 조회 요구에 따라 확정 |
| 문서 버전 | 레지스트리 일부 버전 공란 | 메타데이터 담당자와 시행일·개정·과거본 처리 기준 확인 |

## 8. 미확정 결정과 필요한 확인

아래 사항은 초안에서 임의로 확정하지 않는다.

1. **ID 계약:** 레지스트리의 실제 ID 형식이 메타데이터 담당자와 합의된 기준인지, 레지스트리에 임시 발급된 문서가 있는지 확인한다.
2. **정본·버전:** 동일 규정의 과거본·현행본·시행예정본과 OCR 중복본을 어떤 기준으로 보존·조회할지 정한다.
3. **청크와 규정 노드의 관계:** 모든 조항 청크를 Provision 노드로 만들지, 특정 유형만 노드화할지 확정한다.
4. **위반 유형 체계:** 백엔드 API 부록 D의 violationCode 목록을 초기 허용 코드표로 삼고, 최신 법령·고시와 대조한 뒤 코드표의 관리·개정 버전을 확정한다.
5. **표현 정규화:** 원문 표현과 정규화 표현의 저장 위치, 같은 표현의 문서 간 병합 기준을 정한다.
6. **원료 키와 범위:** 일반 식품 원료와 건강기능식품 기능성 원료를 어떤 기준으로 같은 개념으로 연결할지 확인한다.
7. **사례 범위:** 위반사례 DB 전량 적재 여부, 원본 레코드 기본키, 개인정보·업소 식별자 처리 범위를 확정한다.
8. **절차 근거:** 팀이 합의한 시스템 흐름도를 SOP(표준 업무 절차) 기준으로 사용한다. 최신 백엔드 API 설계서 v0.4는 상태값·버전·저장 규칙을 보완하는 상세 계약으로 취급한다. 양쪽 내용이 다르면 차이를 임의로 합치지 말고 담당 팀에 확인한 뒤 확정한다.
9. **Neo4j 버전:** 이는 설치해 사용할 그래프 데이터베이스 제품의 배포 버전(예: 5.x 계열)을 뜻하며, 문서 버전이나 온톨로지 버전이 아니다. 논리 스키마 초안에는 필요하지 않다. 실제 Neo4j용 제약·인덱스·적재 쿼리를 작성할 때 설치 환경에 맞추기 위해 그때 확인한다.
10. **엔터티 범위:** 최신 백엔드 설계서의 8종 구분(백엔드 테이블 관리 2종, 온톨로지 관리 6종)과 온톨로지 설계서의 추가 후보 클래스를 대조하고, 제품·업체·광고·판정 같은 API 데이터를 그래프에 복제할 필요가 있는지 결정한다.
11. **Agent 실행 로그:** 멀티에이전트 메모의 도구 선택·실행 경로 기록과 백엔드 콜백/저장 필드 사이의 계약을 합의한다.
12. **Neo4j 실행 환경:** 제출용 Cypher와 제약·인덱스를 실행할 실제 Neo4j 버전·에디션·테스트 DB를 확인한다. 현재 구문은 5.x 계열 가정의 초안이다.

## 9. 인수 및 검증 기준

청킹 결과를 반영한 뒤 다음을 확인하고 이 문서의 미확정 표시를 갱신한다.

- 모든 Document가 레지스트리의 고유 document_id와 연결된다.
- 모든 Chunk의 chunk_id가 유일하고, 설정된 parent_id가 존재하며 같은 문서에 속한다.
- 조항·페이지·레코드 위치로 원문을 찾아갈 수 있고, 대표 청크를 원문과 대조해 번호·숫자·특수문자·표현이 보존되었음을 확인한다.
- 모든 도메인 관계가 실제 청크를 인용하는 Evidence와 연결된다.
- 온톨로지의 클래스·관계·속성이 Neo4j 라벨·관계·속성에 빠짐없이 매핑되고, 실제 법령 기반 S-P-O마다 원문 source_chunk_id와 source_span이 연결된다.
- 고유 제약은 안정 키의 null·중복 검증 후 적용하고, 인덱스마다 실제 조회 패턴을 설명한다. 제출 Cypher는 팀 Neo4j 버전에서 실행 확인한다.
- 멀티홉 질의는 각 단계 근거와 문서 버전을 반환하고, 심의·법무 담당자가 결과의 사용 범위와 한계를 검토한다.
- 위반 유형, 원료, 표현의 식별·병합 기준이 문서화되고, 이름만 근거로 사실 관계를 합치지 않는다.
- 절차 그래프의 단계 순서·담당·조건은 팀 합의 시스템 흐름도를 기준으로 하고, API DOCX v0.4와 다른 부분은 확인 기록을 남겨 확정한다.
- 레지스트리, 메타데이터 담당자, 온톨로지 담당자가 같은 ID와 버전 기준을 사용한다.

## 10. 참고 자료

- C:\Users\Playdata\Downloads\청킹 담당자 전달 브리프.md — 포맷별 청킹 규칙, 허용 chunk_type, 완료 기준
- docs/청킹_보완_필요.md — 통합 산출물, 원문 근거 필드, ID 계약 보완 요청
- data/document_registry.csv — 문서 ID·원본 경로·제목·버전·청킹 파일 목록
- docs/EDA_결과_보고서_v0.2.md — 데이터 프로파일링 및 원료 식별자 주의사항
- C:\Users\Playdata\Desktop\멀티에이전트 설계.txt — supervisor, 검색·판정·추천 역할과 stage별 실행 규칙
- C:\Users\Playdata\Downloads\[도메인온톨로지] MLE_도메인_온톨로지_설계서_v0.1.docx — 후보 클래스·관계·CQ; 문서가 예시 값을 가상이라고 명시
- C:\Users\Playdata\Downloads\★백엔드 API 설계서 v5.0_수정.docx — 최신 ERD·상태 전이·보고서 버전·보존 규칙의 기준 자료
- C:\Users\Playdata\Downloads\★백엔드 API 설계서_흐름도 v5.0 반영.pdf — 이전 흐름 참고 자료; 직접 재작성·삭제 정책 등 새 수정본과 충돌하는 내용은 구버전으로 취급
- 첨부 흐름도 이미지 — AI 심의, 적합·부적합 분기, 후속 조치와 법무 의견 전달의 시각적 흐름

