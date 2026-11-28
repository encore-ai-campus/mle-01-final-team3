# 개체와 관계 추출 JSON 설계

## 목적과 범위

이 설계는 사용자가 제품명과 광고 문구를 입력하면 검토 표현을 추출하고, 관련 위반 유형·법령 조항·사례를 검색해 출처와 함께 결과를 만드는 데 필요한 추출 데이터를 정의한다. 원문 청크는 입력 자료로 유지하고, 이 문서의 별도 JSON Schema에 맞춰 개체·관계 결과를 저장한다.

추출 단계는 광고의 법 위반을 확정하지 않는다. 문구와 위반 유형·조항 간 검색 연결은 후보로 표시할 수 있으며, 출처가 직접 뒷받침하는 사실 및 승인된 내부 판단과 구분한다. 법정 심의 결과나 행정처분을 대신하지 않는다.

설계 입력은 온톨로지 v1.0의 클래스·관계, `data/data_chunking/chunk_schema.json`, `data/data_chunking/manifest.json`, `data/data_chunking/document_registry.csv`, `data/data_chunking/structured_chunks.jsonl`, 백엔드 `ReviewCreate`·`Finding`·`Source` 및 `ReviewRun`·`Report`·`LegalSubmission` 구조다. 온톨로지·사례 클래스와 관계는 실제 자료로 검증하면서 확정한다.

## 데이터에서 확인한 사실

- 청크 릴리스는 문서 453개, 청크 2,256,998건이며 `source_id=document_id`, `source_chunk_id=chunk_id` 일치와 `source_span`, 조항 위치 필드를 사용한다. 페이지는 없는 문서에서 null일 수 있다.
- 청킹 스키마는 `product`, `product_with_raw_materials`, `raw_material`, `raw_material_metadata` 레코드 종류와 `link_status`를 정의한다.
- `DOC-D1DABDE9E3:PRODUCT_WITH_RAW_MATERIALS:1997040105528`에는 `PRDLST_REPORT_NO`, `BSSH_NM`, `LCNS_NO`, `RAWMTRL_NM`이 한 레코드에 들어 있고 `link_status=confirmed_from_same_record_product_raw_material_fields`다. 제품과 원료의 같은 레코드 내 관계를 지지한다. 원료 마스터와 제품 원료 문자열의 동일 개체 병합까지 증명하지는 않는다.
- `389128677e1eb090` 기능성 원료 인정 레코드에는 인정번호(`HF_FNCLTY_MTRAL_RCOGN_NO`), 적용 원료(`APLC_RAWMTRL_NM`), 기능성 내용(`FNCLTY_CN`), 섭취량·주의사항 필드가 있다. 원료와 인정 기능성의 연결은 그 레코드에 함께 있는 범위에서 추출할 수 있다.
- `3e85ebc3edc60881:R0000001` 식품원료 레코드는 `Abiu열매`, 영문명·학명·사용 가능 부위를 제공하지만 제품 연결 필드는 없다. 이 청크만으로 Product 관계를 만들지 않는다.
- 사례 청크 `fdb75433e5ba9e14:PG061:S0127`은 사례집에서 식품표시광고법 제8조 제1항 제5호와 소비자를 기만하는 표시·광고를 함께 적는다. 법령 청크 `7d237411cc7cb62e:A008:P001:I005`에는 해당 호의 법문이 있다. 이는 관계가 여러 출처의 근거를 가질 수 있는 예다.
- 사례집 OCR 청크 `fc1959b68d6d1e90:PG022:S0055`에서 `체중감소약` 표현을 확인할 수 있지만 주변 OCR 문구가 손상돼 있다. 예시에서는 표현과 사례 관계를 검토 대기 후보로 둔다.
- 백엔드 입력은 검토 제목(제품명), 제품 분류, 원문 광고 문구를 받는다. 보고서 finding에는 문장 ID·판정·근거·위반 코드·사례가 있지만, 현재 `Source` 계약에는 `document_id`, `chunk_id`, `source_span`이 없다. 보고서의 법령 제목·조항·URL만으로 청크 단위 출처를 재현할 수 없으므로 에이전트 연동에서 source chunk 식별값을 전달할지 후속 합의가 필요하다.
- `data/ontology_validation/law_violation_mapping.json`은 법 제8조 제1항 1~5호만 매핑한 부분 매핑이다. 원문 제8조 제1항에는 1~10호가 있으므로 이 파일을 전체 허용 코드표로 간주하지 않는다. 해당 파일과 테스트 fixture는 본 작업에서 수정하지 않았다.

## 추출 대상

| 개체 | 추출 목적·범위 | 식별·출처 원칙 |
|---|---|---|
| LegalProvision | 입력 표현과 관련 조항을 검색하고 검토 근거 제시 | 문서·시행 버전, 조·항·호·목, 원문 청크를 보존 |
| ViolationType | 표현과 관련해 검색할 표준 분류와 그 정의 제공 | 공식 코드가 확인되면 코드 체계와 함께 저장. 분류 체계 자체와 광고별 적용 후보를 구분 |
| AdvertisementClaim | 광고 원문에서 검토할 문장·구절 | 원문 표현과 정규화 표현 분리, 광고 또는 사례 출처와 원문 위치 보존 |
| Ingredient | 원료 설명과 식별 정보 검색 | 이름·영문명·학명·설명·사용 조건을 출처와 함께 보존. 자료가 명시할 때만 FunctionalClaim 연결 |
| Case | 유사 사례 검색 | 개별 사례 ID가 없으면 source document/chunk를 임시 식별 기준으로 사용. Case 노드화 여부는 그래프 단계에서 확정 |
| FunctionalClaim / AllowedPhrase | 제품·원료 정보와 기능성 문구 검색 경로를 지원 | 인정 내용과 광고에 허용되는 문구는 같은 값이라고 가정하지 않음. 공식 출처·조건 확인 후 구별 |

제품·업체는 사용자가 제품명을 넣었을 때 제품을 찾고 원료 정보를 조회하는 연결 대상으로 포함한다. 검토 실행·판정·법무 의견·후속 업무는 정적 문서 추출 대상이 아니라 백엔드 런타임 데이터다.

## 관계별 근거와 추출 방법

아래 상태는 초기 데이터 대조 결과다. `확인`은 예시 청크 또는 구조화 필드에서 관계를 뒷받침하는 근거를 찾았다는 뜻이며, 전체 데이터셋에 대한 전수 관계 검증을 뜻하지 않는다. `조건부`·`미확인` 관계는 자동 확정하면 안 된다.

| 관계·방향·의미 | 카디널리티 / 제약 | 근거 기준 / 확인한 데이터 위치 | 추출 방식 | 직접성 / 초기 상태 | 검토 규칙 |
|---|---|---|---|---|---|
| MANUFACTURES<br>Company→Product<br>업체가 제품을 제조·취급 | Company 1 : Product 0..N; Product 1..N 업체. 업체 역할 필요 | 제품 레코드의 업체명·인허가번호·제품 신고번호. 예: `DOC-D1DABDE9E3:PRODUCT_WITH_RAW_MATERIALS:1997040105528` | 구조화 필드 매핑 | 필드는 직접 확인; 역할 관계는 조건부 | `BSSH_NM`만으로 제조·수입·판매 역할 확정 금지. 업종·역할 확인 |
| CONTAINS<br>Product→Ingredient<br>제품에 원료가 포함됨 | Product 1 : Ingredient 1..N; 같은 Ingredient는 여러 Product에 연결 가능 | 같은 제품 레코드의 `PRDLST_REPORT_NO`, `RAWMTRL_NM`; 샘플 link_status는 같은 레코드 필드로 확인 | 원료명 분리·순서 보존 후 구조화 필드 매핑 | 같은 레코드 안 연결은 직접 확인 | 제품 원료 문자열과 원료 마스터 개체 병합은 별도 검증 |
| HAS_CLAIM<br>Ingredient→FunctionalClaim<br>원료의 인정 기능성 | Ingredient 0..N : FunctionalClaim 0..N | 기능성 원료 인정 레코드의 인정번호·적용 원료명·기능성 내용·인정일 | 공식 구조화 레코드 필드 매핑 | 같은 인정 레코드의 필드 연결 확인 | 인정번호만으로 식별하지 않고 적용 원료·유효기간 확인 |
| ALLOWS<br>FunctionalClaim→AllowedPhrase<br>인정 기능성에 허용된 표현 | FunctionalClaim 1..N : AllowedPhrase 0..N | 공식 자료가 기능성에 허용되는 문구와 조건을 명시해야 함. `FNCLTY_CN`만으로 허용 여부 확인 불가 | 공식 문구·조건 추출 후 인정 정보와 매핑 | 미확인 | 인정 기능성 문구를 광고 허용 문구로 자동 간주하지 않음 |
| ADVERTISED_AS<br>Product→Advertisement<br>제품이 광고됨 | Product 1 : Advertisement 0..N; 다제품 광고면 N:M | 입력 제품명과 제품 식별자가 일치하는 검토 요청 | 제품명 검색·식별자 해소 후 런타임 연결 | 런타임 생성 | 입력 title은 이름 문자열이므로 복수 후보는 미해결/확인 필요 |
| HAS_CLAIM<br>Advertisement→AdvertisementClaim<br>광고 안에 표현이 포함됨 | Advertisement 1 : AdvertisementClaim 1..N; 표현은 원문 구간별 식별 | 제출 광고 원문과 문자 위치 | 표현 추출 후 원문 오프셋 생성 | 런타임 생성 | 원문 인용·시작·끝 위치 보존; 정규화 표현 분리 |
| INDICATES_RISK_OF<br>ReviewDecision→ViolationType<br>판정이 위험 유형을 제시 | ReviewDecision 1 : ViolationType 0..N | 실행 보고서 finding의 판정·위반 코드 | 검색 후보 매핑 및 판정 결과 기록 | 런타임 생성 | 위험 후보이며 확정 위반·행정처분이 아님 |
| DETERMINES<br>승인된 ReviewDecision→ViolationType<br>승인된 내부 판정의 분류 | ReviewDecision 1 : ViolationType 0..N | 승인 권한·상태가 명시된 내부 승인 기록 | 승인 이벤트/상태 매핑 | 미확인 | 별도 승인 상태가 확인되지 않음. AI 결과만으로 생성 금지 |
| DEFINED_BY<br>ViolationType→LegalProvision<br>위반 유형의 법령 근거 | ViolationType 1..N : LegalProvision 0..N; 버전별 유효기간 필요 | 공식 분류표·법령 연결. `fdb75433e5ba9e14:PG061:S0127`, `7d237411cc7cb62e:A008:P001:I005`가 제8조제1항제5호 예시 | 규칙/큐레이션 매핑, 양쪽 청크 인용 | 예시에서 직접 연결 확인 | 코드·코드체계와 조항 검증. 기존 매핑 파일은 1~5호만 포함 |
| SUPPORTED_BY<br>ReviewDecision→Evidence<br>판정 근거 | ReviewDecision 1 : Evidence 1..N | finding의 rationale/source가 실제 사용한 출처를 가리킴 | 에이전트 출처를 Evidence로 만들고 연결 | 런타임 생성 | API Source에 청크 키 없음. source_id/chunk_id/span 연동 필요 |
| EVIDENCE_FROM<br>Evidence→LegalProvision 또는 LegalDocument<br>근거의 출처 | Evidence 1 : 출처 1 | 청크와 조항 또는 문서 레지스트리로 역추적 가능한 인용 | document_id/chunk_id/source_span 복사 후 조항 매핑 | 입력 구조에서 연결 가능 | source_id=document_id, source_chunk_id=chunk_id 유지. 조항 불명확하면 문서에 연결 |
| HAS_LEGAL_REVIEW<br>ReviewDecision→LegalReview<br>법무 검토 이력 | ReviewDecision 1 : LegalReview 0..N | LegalSubmission의 report_run_id·상태·검토 시각 | 백엔드 런타임 외래키 매핑 | 런타임 생성 | 요청 상태와 실제 법무 의견 구분. LegalSubmission이 검토 결과 전체는 아님 |
| REQUIRES_FOLLOW_UP<br>LegalReview→FollowUpTask<br>법무 검토 후속 업무 | LegalReview 1 : FollowUpTask 0..N | 검토가 생성한 task ID·내용·담당·상태 | 업무 데이터 ID 연결 | 미확인 | 현재 백엔드에서 FollowUpTask 엔터티 미확인 |
| GENERATES_TASK<br>ReviewDecision→FollowUpTask<br>판정에 따른 내부 업무 | ReviewDecision 1 : FollowUpTask 0..N | 판정으로 실제 생성된 업무 레코드 | 판정·업무 ID 연결 | 미확인 | 업무 모델·생성 규칙 합의 전 생성 금지 |
| PART_OF<br>LegalProvision→LegalDocument<br>조항이 속한 문서 버전 | LegalProvision N : LegalDocument 1 | 조항 청크의 document_id와 문서 레지스트리 | 청크 document_id 및 조항 위치 필드 매핑 | 입력 구조에서 연결 가능 | 레지스트리 버전 공란은 미확정으로 유지 |
| ISSUED_FOR<br>EnforcementAction→Advertisement 또는 Company<br>처분 대상 | EnforcementAction 1 : 대상 1..N | 식품안전나라 위반사례 레코드의 처분·대상 업체 정보 | 처분 필드 매핑, 업체 번호로 Company 해소 | 업체는 조건부; 광고는 미확인 | 업체 처분을 광고 처분으로 확대하지 않음. 광고 ID가 원자료에 있을 때만 연결 |
| REVIEWED_AS<br>Advertisement→ReviewDecision<br>광고에 대한 판정 이력 | Advertisement 1 : ReviewDecision 0..N; Decision은 Advertisement 1개 | 백엔드 report의 review_id/run_id | 런타임 ID 매핑 | 런타임 생성 | 재심의 결과를 버전별로 누적 |
| ANALYZES<br>ReviewDecision→AdvertisementClaim<br>판정이 분석한 표현 | ReviewDecision 1 : AdvertisementClaim 1..N | finding sentence_id/text와 원문 표현 ID·위치 | finding ID와 claim offset 매핑 | 런타임; 현재 API에 claim ID/offset 없음 | 텍스트 동일성만으로 연결 금지 |
| PRODUCES<br>ReviewRun→ReviewDecision<br>실행이 생성한 판정 | ReviewRun 1 : ReviewDecision 1; Decision은 Run 1개 | Report.run_id 외래키 | 백엔드 외래키 매핑 | 런타임 생성 | 판정 보고서와 판정 없는 RA_SUGGEST 구분 |
| CONTAINS_EXPRESSION<br>Case→AdvertisementClaim<br>사례 원문에 광고 표현 포함 | Case 1 : AdvertisementClaim 0..N; 표현은 여러 사례에 재사용 가능 | 사례 청크의 실제 광고 문구·위치. OCR 예: `fc1959b68d6d1e90:PG022:S0055` | 사례 청크에서 표현·위치 추출 | 표현 원문은 보이나 OCR 때문에 조건부 | OCR 표현 검토 대기; 사례별 실제 문구 보존 |
| CLASSIFIED_AS<br>Case→ViolationType<br>사례에 기록된 위반 유형 | Case 1 : ViolationType 0..N; 유형은 여러 사례에 연결 가능 | 사례가 코드·분류를 명시한 경우. 예: `fdb75433e5ba9e14:PG061:S0127` | 분류 코드 매핑 | 일부 사례 청크에서 직접 확인 | 출처에 명시된 유형만 연결; 표현 유사도만으로 추정 금지 |
| GROUNDED_IN<br>Case→LegalProvision<br>사례가 인용한 근거 조항 | Case 1 : LegalProvision 0..N; 조항은 여러 사례가 공유 가능 | 사례가 조항을 명시한 경우. 예: `fdb75433e5ba9e14:PG061:S0127` | 조항 인용 파싱 후 법령 청크 연결 | 일부 사례 청크에서 직접 확인 | 사례의 인용 법령 버전과 현행본 구분 |

Case는 온톨로지에 별도 클래스로 고정되지 않았으므로 이 관계들은 추출 계약의 후보다. 별도 Case 노드 대신 사례 문서·청크를 검색 원본으로 삼는다면 이 관계의 주체를 SourceRecord/Chunk로 조정한다.

## 추출 JSON 계약

별도 JSON Schema는 `data/data_extraction/extraction_result.schema.json`이다. 입력 청크는 기존 `data/data_chunking/chunk_schema.json` 그대로 둔다. 추출 결과는 단일 청크 결과일 수도 있고 여러 청크를 근거로 한 관계일 수도 있으므로, 아래 계약은 결과와 각 관계의 근거에 source reference를 둔다.

### 주요 필드

| 필드 | 의미 |
|---|---|
| schema_version, extraction_id | 스키마 버전과 추출 레코드 식별자 |
| source | 추출을 시작한 입력 청크 참조 |
| relationship_result | found / none_found / partial / not_evaluated. 관계가 없으면 relationships는 빈 배열 |
| entities | 원문 mention, 표준화 값, 공식 ID(없으면 null), 개체 상태와 근거 |
| relationships | subject/predicate/object, 근거 유형, 추출 방식, 상태, 검토 상태, 적용 범위와 근거 청크 목록 |
| evidence | document_id/chunk_id/source_span/page, 직접 확인한 quote, evidence_type |

초기 관계 상태는 `source_confirmed`, `system_candidate`, `human_confirmed`, `unresolved`로 둔다. 근거 유형은 `direct_text`, `structured_field`, `curated_mapping`, `retrieval_result`, `model_inference` 계열로 구분한다. “관계 없음”은 추측 관계를 추가하지 않고 `relationship_result=none_found`, `relationships=[]`로 기록한다. 이는 해당 청크에서 관계를 찾지 못했다는 뜻이지 전체 그래프에서 관계가 없다는 뜻이 아니다.

공식 ID와 내부 추출 ID를 분리한다. 공식 ID가 있으면 `official_id`에 그대로 저장하고, 없으면 entity_id를 `document_id:chunk_id:entity_type:순번`처럼 출처 기반으로 발급한다. 다른 문서에 같은 명칭이 나온다고 자동 병합하지 않는다.

## 예시와 검증 범위

`data/data_extraction/extraction_examples.json`에 실제 데이터 기반 네 가지 시나리오를 넣었다.

1. **정상 관계:** 제품 원료 레코드의 명시적 필드에서 Product→Ingredient CONTAINS를 추출
2. **불확실:** OCR 사례의 표현·사례 관계를 candidate/pending으로 기록
3. **관계 없음:** 단독 원료 레코드에서 원료 개체만 추출하고 관계 배열은 빈 값으로 둠
4. **복수 근거:** 사례집의 조항·분류 연결과 법률 조항 청크로 같은 DEFINED_BY 주장을 뒷받침

각 sample의 출처 경로와 청크 ID는 `structured_chunks.jsonl`의 레코드 및 `chunking_samples_50.md`와 대조한다. OCR 예시는 원문 품질이 완전하지 않아 검토 대기 상태다. 예시는 그래프 적재 사실이나 법률 판정 결과가 아니라 JSON 계약을 보여주는 샘플이다.

## 다음 합의 항목

1. Case를 독립 엔터티로 둘지 사례 원문 청크/레코드로 둘지 결정
2. 백엔드 Source에 document_id, chunk_id, source_span을 추가하거나 검색 실행 로그를 통해 보고서 finding까지 근거를 전달
3. violation code와 법령 조항의 전체 매핑을 최신 법령·시행령 별표와 대조. 현재 validation mapping은 일부 호만 포함
4. ALLOWS 관계의 공식 허용 문구 출처 및 적용 조건 확정
5. `system_candidate`와 `human_confirmed` 사이 승인자·승인 이벤트를 업무 흐름에 맞게 정의
6. 공식 ID가 없는 표현·사례·원료의 내부 ID와 개체 병합 검토 절차 확정

