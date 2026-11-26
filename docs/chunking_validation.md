# 청킹 결과 검증

- 생성 청크: 2190390개
- 문서: 51개
- 중복 chunk_id: 0개
- 잘못된 참조: 0개
- 대표 샘플: 50개
- 카탈로그 청크: 2175919개

## 기준
- document_id는 `data/document_registry.csv`의 값을 사용했습니다.
- 구조화 법령·행정규칙을 우선하고 OCR 중복은 품질 로그에 기록했습니다.
- 법령 ID는 `문서ID:A조:P항:I호:M목` 계층을 사용했습니다.
- OCR은 페이지가 아닌 의미 단위로 분할하고 source_page/source_span을 기록했습니다.
- C002/I1250은 `PRDLST_REPORT_NO`를 `original_id`로 사용하고, `source_record_number`는 추적용으로만 사용했습니다.
- 카탈로그의 상품·원료 연결은 동일 원본 레코드의 원료 필드가 있을 때만 확인으로 표시했습니다.

## 카탈로그 검증

- C002 document_id: `DOC-D1DABDE9E3`
- I1250 document_id: `DOC-8E5CFCD60A`
- 원본 ID 필드: `PRDLST_REPORT_NO`
- 상품 타입: `product`, 원료 타입: `raw_material`
- 연결 상태가 확인되지 않는 레코드는 `link_status`에 별도 표시했습니다.

## 대표 샘플 원문 대조

아래 샘플은 각 청크의 `text`가 `source_path`의 파싱 원문에서 추출된 텍스트이며, `source_span`/`source_page`로 역추적할 수 있습니다.

- `bb51bc2a5017baec:PG001:S001` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 1`
- `bb51bc2a5017baec:PG001:S002` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 1`
- `bb51bc2a5017baec:PG001:S003` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 1`
- `bb51bc2a5017baec:PG001:S004` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 1`
- `bb51bc2a5017baec:PG001:S005` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 1`
- `bb51bc2a5017baec:PG001:S006` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 1`
- `bb51bc2a5017baec:PG002:S007` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 2`
- `bb51bc2a5017baec:PG002:S008` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 2`
- `bb51bc2a5017baec:PG002:S009` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 2`
- `bb51bc2a5017baec:PG003:S010` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 3`
- `bb51bc2a5017baec:PG003:S011` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 3`
- `bb51bc2a5017baec:PG003:S012` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 3`
- `bb51bc2a5017baec:PG003:S013` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 3`
- `bb51bc2a5017baec:PG003:S014` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 3`
- `bb51bc2a5017baec:PG004:S015` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 4`
- `bb51bc2a5017baec:PG004:S016` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 4`
- `bb51bc2a5017baec:PG004:S017` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`, span `page 4`
- `cbfc8683ba236d34:PG001:S001` (guide): source `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/현재/★++「식품등의+부당한+표시+또는+광고의+내용+기준」+고시+전문(제2025-79호,+2025.12.4.json`, span `page 1`
- `5080265feb5e1e6f:PG001:S001` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S002` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S003` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S004` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S005` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S006` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S007` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S008` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S009` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S010` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S011` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S012` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S013` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S014` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S015` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG001:S016` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 1`
- `5080265feb5e1e6f:PG002:S017` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 2`
- `5080265feb5e1e6f:PG002:S018` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 2`
- `5080265feb5e1e6f:PG002:S019` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 2`
- `5080265feb5e1e6f:PG002:S020` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 2`
- `5080265feb5e1e6f:PG002:S021` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 2`
- `5080265feb5e1e6f:PG002:S022` (guide): source `data/data_parsing/01_건강기능식품/법령_고시/원본 데이터/시행예정/2028/건강기능식품의 표시기준(식품의약품안전처고시)(제2026-66호)(20280101).json`, span `page 2`
- `DOC-D1DABDE9E3:RAW_MATERIAL:1997040105528` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 1`
- `DOC-D1DABDE9E3:RAW_MATERIAL:2022051450995` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 2`
- `DOC-D1DABDE9E3:RAW_MATERIAL:2022051450994` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 3`
- `DOC-D1DABDE9E3:RAW_MATERIAL:200006190334` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 4`
- `DOC-D1DABDE9E3:RAW_MATERIAL:1999029407029` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 5`
- `DOC-D1DABDE9E3:RAW_MATERIAL:201300150794` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 6`
- `DOC-D1DABDE9E3:RAW_MATERIAL:1997040105515` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 7`
- `DOC-D1DABDE9E3:RAW_MATERIAL:201800124108` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 8`
- `DOC-D1DABDE9E3:RAW_MATERIAL:20010306244397` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 9`
- `DOC-D1DABDE9E3:RAW_MATERIAL:2004029461410` (record): source `data/data_parsing/02_일반식품/원본 데이터/C002/C002_261123.json`, span `record 10`
