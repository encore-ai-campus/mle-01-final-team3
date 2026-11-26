# 청킹 결과 검증

- 생성 청크: 2236785개
- 문서: 54개
- 중복 chunk_id: 473개
- 빈 청크 제외: 107개
- 잘못된 참조: 0개
- 대표 샘플: 28개
- 카탈로그 청크: 2222421개

## ID·참조 무결성

- ID 해시: `041f9e1dcb0076cae4c43d1c19a6b4eb35c5e4a7d00778a1ba8589bb2d53c07d`
- source_chunk_id 해시: `041f9e1dcb0076cae4c43d1c19a6b4eb35c5e4a7d00778a1ba8589bb2d53c07d`
- 참조 해시: `aedb0ae3bcc42590c6706db7cd79b1200d868e59454419331dc5dddacf234e16`
- 재실행 ID 해시: **MATCH**
- 중복 ID: 0개
- 잘못된 parent_id: 461개
- 잘못된 source_chunk_id: 0개

## 기준
- document_id는 `data/document_registry.csv`의 값을 사용했습니다.
- 구조화 법령·행정규칙을 우선하고 OCR 중복은 품질 로그에 기록했습니다.
- 법령 ID는 `문서ID:A조:P항:I호:M목` 계층을 사용했습니다.
- OCR은 페이지가 아닌 의미 단위로 분할하고 source_page/source_span을 기록했습니다.
- C002/I1250은 `PRDLST_REPORT_NO`를 제품 보고서 ID로 사용하고, 원재료 필드는 동일 제품 레코드의 속성으로 보존했습니다.
- I0030은 제품 레코드, `food_raw_material_metadata`는 원료 메타데이터 레코드로 처리했습니다.
- 충돌 ID는 발생 순서별 접미사를 부여하고 parent_id/source_chunk_id 참조를 재매핑했습니다.

## 카탈로그 검증

- C002 document_id: `DOC-D1DABDE9E3`
- I1250 document_id: `DOC-8E5CFCD60A`
- I0030 document_id: `DOC-6A72EB6512`
- food_raw_material_metadata document_id: `d5de46c63314d48d`
- C002/I1250/I0030 원본 ID 필드: `PRDLST_REPORT_NO` (제품 보고서 ID)
- C002 타입: `product_with_raw_materials`
- I1250/I0030 타입: `product`
- food_raw_material_metadata 타입: `raw_material`

## 대표 샘플 원문 대조

아래 샘플은 각 청크의 `text`가 `source_path`의 파싱 원문에서 추출된 텍스트이며, `source_span`/`source_page`로 역추적할 수 있습니다.

- `cbfc8683ba236d34:PG001:S001` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/현재/★++「식품등의+부당한+표시+또는+광고의+내용+기준」+고시+전문(제2025-79호,+2025.12.4.json`, span `page 1`
- `5080265feb5e1e6f:PG001:S001` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S002` (article): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S003` (article): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S004` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S005` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S006` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S007` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S008` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S009` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S010` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S011` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `f32c7bd98edadb61:PG001:S001` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 1`
- `f32c7bd98edadb61:PG001:S002` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 1`
- `f32c7bd98edadb61:PG001:S003` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 1`
- `f32c7bd98edadb61:PG003:S004` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 3`
- `f32c7bd98edadb61:PG003:S005` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 3`
- `f32c7bd98edadb61:PG014:S006` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 14`
- `f32c7bd98edadb61:PG014:S007` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 14`
- `f32c7bd98edadb61:PG014:S008` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 14`
- `f32c7bd98edadb61:PG014:S009` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 14`
- `f32c7bd98edadb61:PG015:S010` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 15`
- `f32c7bd98edadb61:PG015:S011` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 15`
- `f32c7bd98edadb61:PG015:S012` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 15`
- `f32c7bd98edadb61:PG015:S013` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 15`
- `f32c7bd98edadb61:PG017:S014` (article): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 17`
- `f32c7bd98edadb61:PG018:S015` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 18`
- `f32c7bd98edadb61:PG018:S016` (guide): source `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`, span `page 18`
