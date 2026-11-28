# Neo4j 그래프 스키마 설계서 — 보완 초안

- 기준일: 2026-11-27
- 범위: 규정 그래프 + 심의 절차 그래프
- 상태: 논리 설계 확정, Neo4j 실행 검증 전
- 우선 기준: `[도메인온톨로지] MLE_도메인_온톨로지_설계서_v1.1.pdf`, 최신 백엔드 검토 흐름 v5.2, 팀 합의 흐름도

> `data/data_chunking_v2`의 대용량 본체는 현재 `structured_chunks-001.jsonl.crdownload` 상태이다. 따라서 이 문서는 v2의 `chunk_schema.json`·`chunking_quality_log.jsonl`, 작업공간에 동기화된 구조화 청크, EDA 및 최신 백엔드 문서를 대조해 작성했다. 본체가 완전히 내려받아지면 아래의 미검증 항목을 재검증한다.

## 1. 설계 원칙

1. `document_id`, `chunk_id`, `parent_id` 계층과 `PRDLST_REPORT_NO`, `LCNS_NO` 조인은 원본 키로 확인되는 관계로만 적재한다.
2. 광고 표현–위반 유형–법령 조항, 원재료–기능성–제품 등의 의미 관계는 원문 추출·검증 후에만 적재한다. 공출현·문자열 유사성은 확정 근거가 아니다.
3. 모든 의미 엣지는 `Evidence`를 통해 `source_chunk_id`, 원문 인용, 검증 상태를 보존한다.
4. 확정되지 않은 키에는 uniqueness constraint를 걸지 않는다.
5. 온톨로지 v1.1 명칭을 우선한다. v0.1 초안의 후보 명칭은 별칭 또는 마이그레이션 대상으로만 취급한다.

## 2. 데이터 검증 결과와 예외

| 항목 | 확인 결과 | 스키마 반영 |
|---|---|---|
| v2 청크 품질 | 2,256,998 chunks, 453 documents, duplicate `chunk_id` 0, invalid reference 0, empty text 0, ID rewrite 512 | v2 본체 완전 수신 후 재검증 |
| 문서–청크 계층 | `document_id`, `chunk_id`, `parent_id` 제공 | `Document-[:HAS_CHUNK]->Chunk`, `Chunk-[:CHILD_OF]->Chunk` |
| C002–I1250 | `PRDLST_REPORT_NO` 공통 1,087,872건, 한쪽만 존재 175건 | `MATCHED`, `C002_ONLY`, `I1250_ONLY` 상태 저장 |
| 제품–업체 | `PRDLST_REPORT_NO` 제품 키, `LCNS_NO` 업체 연결 필드 | 키 일치분만 `MANUFACTURES` |
| 식품원료 | 공식 고유키 확인 불가 | 원료명 단독 uniqueness 금지 |
| 위반사례 | `DSPSDTLS_SEQ` 중복 존재 | 단독 키 금지, 사건 수와 청크 수 분리 |
| 기능성 인정 | 인정번호 중복 가능 | 인정번호 단독 uniqueness 금지 |

## 3. 공통 노드·근거 모델

| 라벨 | 식별키 | 주요 속성 | 원본 필드/근거 | 확정 여부 |
|---|---|---|---|---|
| `Document` | `document_id` | `title`, `version`, `source_path`, `status` | `document_registry.csv`, 청크 메타데이터 | 확정 |
| `Chunk` | `chunk_id` | `document_id`, `parent_id`, `chunk_type`, `text`, `source_page`, `source_span`, `article`, `paragraph`, `item`, `subitem` | v2 `structured_chunks`, `chunk_schema.json` | 확정(본체 재검증 필요) |
| `Evidence` | `evidence_id` | `predicate`, `source_chunk_id`, `quote`, `polarity`, `confidence`, `verification_status`, `verified_by`, `verified_at` | 원문 청크와 추출·검증 로그 | 설계 확정, 데이터 미확정 |
| `LegalProvision` | `provision_id`(권장: `document_id:chunk_id`) | 조문 위치, 제목, 시행일, 원문 | 법령·고시 청크 | 확정 |
| `Product` | 내부 `product_id`; `PRDLST_REPORT_NO` 보존 | `name`, `product_category`, `legal_product_type`, `report_no` | C002/I1250/I0030 원본 필드 | 조건부 확정 |
| `Company` | 내부 `company_id`; `LCNS_NO` 보존 | `name`, `business_type`, `license_no` | 제품 `LCNS_NO`, `BSSH_NM` | 조건부 확정 |
| `Ingredient` | 내부 `ingredient_id` | `surface_name`, `normalized_name`, `source_system`, `normalization_status` | 원재료 필드, 식품원료 데이터 | 원료명 키 미확정 |
| `FunctionalClaim` | 복합 내부 키 | `claim_text`, `recognition_no`, `raw_material`, 유효기간 | `PRIMARY_FNCLTY`, 인정 자료 | 인정번호 단독키 금지 |
| `Advertisement` | 백엔드 `review_id` | `text`, `product_category`, 제목 | 백엔드 `reviews` | 백엔드 원장 참조 |
| `AdvertisementClaim` | 내부 `claim_id` | `text`, `start_offset`, `end_offset`, `extraction_method` | 광고 원문 추출 | 검증 후 확정 |
| `ViolationType` | 코드 + 버전 | `code`, `name`, `rule_version` | 백엔드 허용 코드표, 법령 근거 | 코드표 대조 필요 |
| `ReviewDecision` | `run_id` 또는 `(review_id, version)` | `decision`, `stage`, `reviewed_text`, `findings` | 백엔드 `reports` | 백엔드 원장 참조 |
| `Case` | 검증된 복합 내부키 | 원본 사건 속성 | 위반사례 자료 | 원본키 미확정 |
| `EnforcementAction` | 검증된 원본 처분키 | `action_type`, `authority`, `issued_at`, `period`, `case_no` | 행정처분 원본 | 원본키 미확정 |
| `LegalReview` | `legal_review_id` | `result`, `reviewer_role`, `reviewed_at`, `comment` | 백엔드 법무 검토 | 참조 모델 |
| `FollowUpTask` | `task_id` | `task_type`, `status`, `assignee_role`, `due_at`, `completed_at` | 백엔드 후속 업무 | 참조 모델 |

### 원본 키 관계와 생성 관계

| 시작 → 관계 → 도착 | 식별 근거/방향 | 주요 속성 | 상태 |
|---|---|---|---|
| `Document -[:HAS_CHUNK]-> Chunk` | `Chunk.document_id = Document.document_id` | `source_system`, `load_version` | 확정 |
| `Chunk -[:CHILD_OF]-> Chunk` | 자식 `parent_id = 부모.chunk_id` | `hierarchy_level` | 확정 |
| `Product -[:SAME_REPORT_NO]-> Product` | 동일 `PRDLST_REPORT_NO` | `join_status`, 좌·우 자료원 | 확정 |
| `Company -[:MANUFACTURES]-> Product` | `Company.LCNS_NO = Product.LCNS_NO` | `role`, `join_status`, `source_field` | 키 일치분 확정 |
| `Product -[:CONTAINS]-> Ingredient` | 원재료 필드 추출 | `raw_text`, `source_chunk_id` | 검증 후 |
| `Ingredient -[:HAS_CLAIM]-> FunctionalClaim` | 기능성 문구·인정자료 대조 | `recognition_no`, `source_chunk_id` | 검증 후 |
| `FunctionalClaim -[:ALLOWS]-> AllowedPhrase` | 허용 원문·조건 대조 | 조건, 유효기간, `evidence_id` | 검증 후 |
| `Advertisement -[:HAS_CLAIM]-> AdvertisementClaim` | 광고 원문 추출 | offset, `source_chunk_id` | 검증 후 |
| `AdvertisementClaim -[:INDICATES_RISK_OF]-> ViolationType` | finding·원문·코드표 일치 | `evidence_id`, confidence | 검증 후 |
| `ReviewDecision -[:DETERMINES]-> ViolationType` | 승인된 내부 판단 | `evidence_id`, reviewer/status | 검수 후 |
| `ViolationType -[:DEFINED_BY]-> LegalProvision` | 적용 조항 원문 확인 | `evidence_id`, 조건, 시행일 | 검증 후 |
| `LegalProvision -[:PART_OF]-> LegalDocument` | 조항과 법령 버전 연결 | effective dates | 원본 문서 확인 |
| `Case -[:CONTAINS_EXPRESSION]-> AdvertisementClaim` | 사례 원문에 표현 명시 | quote, locator, `source_chunk_id` | 원문 확인 후 |
| `Case -[:CLASSIFIED_AS]-> ViolationType` | 사례에 분류 명시 | classification_source, `evidence_id` | 추정 금지 |
| `Case -[:GROUNDED_IN]-> LegalProvision` | 사례에 조항 명시 | locator, effective date | 모호하면 보류 |

### 3.3 Evidence 관련 엣지

| 시작 → 관계 → 끝 | 식별키·관계 방향 | 주요 속성 | 원본 필드 또는 근거 | 확정 여부 |
|---|---|---|---|---|
| 도메인 주체 `-[:ASSERTS]->` `Evidence` | `evidence_id`로 주장과 근거 연결 | `predicate`, `assertion_type`, `confidence`, `review_status` | 추출·검증 트리플 | 설계 확정, 데이터 검증 후 |
| `Evidence -[:OBJECT]->` 도메인 객체 | Evidence의 `subject_id/object_id` | `object_class`, `object_id` | S-P-O 매핑 | 설계 확정, 데이터 검증 후 |
| `Evidence -[:CITES]->` `Chunk` | `Evidence.source_chunk_id = Chunk.chunk_id` | `source_chunk_id`, `quote`, `locator`, `source_span` | v2 청크 | 확정 |
| `Evidence -[:EVIDENCE_FROM]->` `LegalProvision` | 검증된 `provision_id` | `effective_from`, `effective_to`, `locator` | 온톨로지 v1.1 법령 근거 예시 | 원문 확인 후 |
| `ReviewDecision -[:SUPPORTED_BY]->` `Evidence` | `decision_id`·`evidence_id` | `rationale`, `model_version`, `review_status` | 백엔드 finding의 sources | 참조 모델, 검증 후 |

`Evidence-CITES->Chunk`는 원문 추적을 위한 확정 구조이고, 나머지 의미·판단 엣지는 실제 인용문과 검수 상태가 있을 때만 `CONFIRMED`로 올린다. `source_chunk_id`가 없거나 인용문이 주장과 일치하지 않으면 엣지를 생성하지 않고 `UNVERIFIED`로 남긴다.

관계 상태는 `CONFIRMED`, `CANDIDATE`, `REJECTED`, `UNVERIFIED` 중 하나다. `CANDIDATE`와 `UNVERIFIED`는 법적 근거 탐색 결과에 포함하지 않는다.

```text
(subject)-[:ASSERTS {evidence_id}]->(Evidence)
(Evidence)-[:OBJECT]->(object)
(Evidence)-[:CITES {source_chunk_id}]->(Chunk)
```

## 4. 규정 그래프

핵심 경로는 `Advertisement → AdvertisementClaim → ViolationType → LegalProvision → LegalDocument`이다. 제품 확인이 필요한 경우 `Product → Ingredient → FunctionalClaim → AllowedPhrase`를 추가로 탐색한다.

`C002`의 `ETC_RAWMTRL_NM`에 원료명이 있다고 해서 그것이 표준 원료 ID라는 뜻은 아니다. 공식 키가 확인되기 전에는 `surface_name`과 `source_chunk_id`만 보존하고, 원료명 단독 고유 제약이나 자동 병합을 하지 않는다.

## 5. 심의 절차 그래프

절차 정의와 실행 이력을 분리한다. `ReviewProcess`, `ProcessStep`, `ActorRole`, `Condition`, `Outcome`은 절차 그래프에 두고, `Review`, `ReviewRun`, `ReviewDecision`, `LegalReview`, `FollowUpTask`는 백엔드 원장 참조 노드로 복제할지 설계 선택이다. 기본안은 상태·보고서 원문은 백엔드가 소유하고 Neo4j에는 참조 ID와 검색용 요약만 두는 CQ 모델이다.

| 요소 | 식별키·주요 속성 | 방향 | 근거 | 확정 여부 |
|---|---|---|---|---|
| `ReviewProcess` | `process_id`, `version`, `name` | `ProcessStep-[:STEP_OF]->ReviewProcess` | 팀 흐름도, 백엔드 v5.2 | 확정 |
| `ProcessStep` | `step_id`, `stage`, `owner_role`, `input`, `output` | `ProcessStep-[:NEXT {condition}]->ProcessStep` | 흐름도 + API stage | 확정 |
| `ActorRole` | `MARKETING`, `LEGAL`, `ADMIN`, `AI` | `ActorRole-[:RESPONSIBLE_FOR]->ProcessStep` | 흐름도·권한 | 확정 |
| `Condition` | `condition_id`, 표현식 | `ProcessStep-[:GUARDED_BY]->Condition` | allowedActions·상태 전이 | 확정 |
| `Outcome` | `SUITABLE`, `UNSUITABLE`, `PUBLISHED`, `ENDED`, `CANCELED` | `ProcessStep-[:YIELDS]->Outcome` | 백엔드 계약 | 확정 |
| `ReviewRun` | `run_id`, `review_id`, `stage`, `run_status`, `attempt` | `Review-[:HAS_RUN]->ReviewRun` | 백엔드 v5.2 | 참조 모델 |
| `Suggestion` | `run_id`, `text`, `rationale`, `status` | `ReviewRun-[:PRODUCES]->Suggestion` | RA_SUGGEST 계약 | 참조 모델 |

최신 흐름은 `MARKETING 등록 → AI_SCREENING → 적합이면 법무 요청 또는 END / 부적합이면 RA_SUGGEST 또는 CANCEL → 사용자가 추천 문구 확인 후 RA_RECHECK 선택`이다. `RA_SUGGEST`는 자동 재심의가 아니며, 성공한 `RA_RECHECK`만 같은 Review의 보고서 버전을 올린다. 직접 수정은 기존 Review 취소 후 새 Review다.

## 6. 키·제약조건·인덱스

아래는 Neo4j 5.x 기준 초안이며 실행 미검증이다. `Ingredient.surface_name`, `DSPSDTLS_SEQ`, `FunctionalClaim.recognition_no`에는 uniqueness를 적용하지 않는다.

```cypher
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (n:Document) REQUIRE n.document_id IS UNIQUE;
CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (n:Chunk) REQUIRE n.chunk_id IS UNIQUE;
CREATE CONSTRAINT product_report_no_unique IF NOT EXISTS FOR (n:Product) REQUIRE n.product_id IS UNIQUE;
CREATE CONSTRAINT process_id_unique IF NOT EXISTS FOR (n:ReviewProcess) REQUIRE n.process_id IS UNIQUE;
CREATE CONSTRAINT step_id_unique IF NOT EXISTS FOR (n:ProcessStep) REQUIRE n.step_id IS UNIQUE;
CREATE INDEX document_source_path IF NOT EXISTS FOR (n:Document) ON (n.source_path);
CREATE INDEX chunk_document_id IF NOT EXISTS FOR (n:Chunk) ON (n.document_id);
CREATE INDEX chunk_parent_id IF NOT EXISTS FOR (n:Chunk) ON (n.parent_id);
CREATE INDEX company_license_no IF NOT EXISTS FOR (n:Company) ON (n.company_id);
CREATE INDEX evidence_source_chunk IF NOT EXISTS FOR (n:Evidence) ON (n.source_chunk_id);
CREATE INDEX violation_code IF NOT EXISTS FOR (n:ViolationType) ON (n.code);
CREATE INDEX review_id IF NOT EXISTS FOR (n:Review) ON (n.review_id);
CREATE INDEX review_run_id IF NOT EXISTS FOR (n:ReviewRun) ON (n.run_id);
```

`Product.product_id` 유일 제약은 C002/I1250/I0030의 결측·중복 검증이 통과한 경우에만 적용한다. C002–I1250 조인 결과에는 반드시 `MATCHED` 1,087,872건과 `C002_ONLY`/`I1250_ONLY` 합계 175건을 구분 저장한다.

## 7. 적재·조회 Cypher 예시

```cypher
// 원본 키로만 계층을 연결한다. 실행 미검증.
MERGE (d:Document {document_id:$document_id})
  ON CREATE SET d.title=$title, d.source_path=$source_path
MERGE (c:Chunk {chunk_id:$chunk_id})
SET c.document_id=$document_id, c.parent_id=$parent_id, c.text=$text,
    c.chunk_type=$chunk_type, c.source_chunk_id=$source_chunk_id
MERGE (d)-[:HAS_CHUNK]->(c);

MATCH (child:Chunk {chunk_id:$chunk_id}), (parent:Chunk {chunk_id:$parent_id})
WHERE child.parent_id = parent.chunk_id
MERGE (child)-[:CHILD_OF]->(parent);
```

현재 구조화 청크에서 확인한 실제 근거 예시는 다음과 같다.

- `bb51bc2a5017baec:PG001:S002`: 「식품등의 부당한 표시 또는 광고의 내용 기준」 목적 조항.
- `5080265feb5e1e6f:PG002:S020`: 건강기능식품 표시기준 제4조(표시사항).
- 품질 로그의 ID rewrite 예: `41d87c15dc0db197:A014:P001:I005 → 41d87c15dc0db197:A014:I005`. 최종 ID를 적재하고 이전 ID는 이력으로만 보존한다.

```cypher
// 광고 심의 근거 멀티홉. CONFIRMED만 반환. 실행 미검증.
MATCH (a:Advertisement {advertisement_id:$advertisement_id})-[:HAS_CLAIM]->(e:AdvertisementClaim)
      -[x:INDICATES_RISK_OF {status:'CONFIRMED'}]->(v:ViolationType)
      -[:DEFINED_BY]->(p:LegalProvision)-[:PART_OF]->(ld:LegalDocument)
      <-[:EVIDENCE_FROM]-(ev:Evidence)-[:CITES]->(c:Chunk)
      <-[:HAS_CHUNK]-(d:Document)
RETURN a.advertisement_id, e.text, v.violation_code, v.name, p.provision_id,
       ld.source_id, ev.evidence_id, c.chunk_id AS source_chunk_id,
       c.text AS source_text, ld.title;
```

`EVIDENCE_FROM`는 온톨로지 v1.1의 Evidence–LegalProvision 예시 방향을 따른다. 실제 적재에서 Evidence 연결 방향을 다르게 선택하면 쿼리도 동일한 방향으로 조정한다. 실행 전까지 근거 없는 관계명을 확정하지 않는다.

## 8. Neo4j 실행 검증 상태

실행 환경 확인 결과, 현재 작업공간에는 `neo4j`, `cypher-shell`, Docker가 설치되어 있지 않고 연결 가능한 Neo4j 서버도 확인되지 않았다. 따라서 아래 항목은 **실행 완료가 아닌 미검증**으로 남긴다.

| 검증 대상 | 상태 | 검증 방법/후속 조치 |
|---|---|---|
| `Document`·`Chunk` uniqueness constraint | 미검증 | Neo4j 5.x에서 스키마 Cypher 실행 후 `SHOW CONSTRAINTS` 확인 |
| `Document.source_path`, `Chunk.document_id`, `Chunk.parent_id` 인덱스 | 미검증 | `SHOW INDEXES` 확인 |
| 원본 키 계층 적재 | 미검증 | 대표 `document_id`·`chunk_id`·`parent_id`로 `HAS_CHUNK`·`CHILD_OF` 결과 대조 |
| Evidence `source_chunk_id` 추적 | 미검증 | Evidence → Chunk → Document 멀티홉 결과와 원문 대조 |
| 광고 심의 멀티홉 Cypher | 미검증 | 테스트 광고·판정·근거 데이터를 넣고 `CONFIRMED` 결과만 반환되는지 확인 |

실행 검증 전까지 이 문서의 Cypher는 Neo4j 5.x 문법을 가정한 설계 예시이며, 운영 스키마 생성 완료로 해석하지 않는다.

## 9. 미검증·결정 필요 항목

- v2 본체 수신 후 chunk 수·중복·참조·대표 `source_chunk_id` 재검증.
- 온톨로지 v1.1 클래스·관계명과의 최종 대조, v0.1 잔여 명칭 제거.
- `DSPSDTLS_SEQ` 중복의 사건 식별 규칙 확정. 사례집 청크 수를 사건 수로 사용하지 않음.
- 기능성 인정번호 중복 원인 확인 후 복합키 결정.
- 의미 관계 추출·법무 검수와 `verification_status` 전이 확정.
- 백엔드 `Review`·`ReviewRun`·`Report`·`LegalOpinion` 중복 적재 여부 결정.
- 팀 Neo4j 버전에서 모든 Cypher 실행 검증. 현재는 실행 완료로 표시하지 않음.
