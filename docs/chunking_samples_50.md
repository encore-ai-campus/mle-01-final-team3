# 대표 청크 50건 원문 대조

파싱 원본 JSON/TXT의 청크 문구와 위치를 비교했다. 두 PDF의 레이아웃 수정 결과는 별도 검증 문서에서 확인한다.

- PASS: 50건
- REVIEW: 0건
- FAIL: 0건

## 1. article — PASS

- chunk_id: `c6e1f86dbab0f4c7:PG005:S0009`
- source_path: `data/data_parsing/01_건강기능식품/법령_고시/현재/기준규격/제2026-43호/건강기능식품의 기준 및 규격_(제1~제3)_개정.json`
- source_page: `5` / source_span: `page 5, lines 25-26`
- 판정 근거: full text in OCR lines; start page matched
> 제1조(시행일) 이 고시는 2008년 6월 1일부터 시행 한다.

## 2. article — PASS

- chunk_id: `459be586daf265c7:PG050:S0235`
- source_path: `data/data_parsing/02_일반식품/법령_고시/현재/표시기준/식품등의 표시기준_20260517기준.json`
- source_page: `50` / source_span: `page 50, lines 7-8`
- 판정 근거: full text in OCR lines; start page matched
> 제1조(시행일) 이 고시는 2028년 1월 1일부터 시행한다. 다만, Ⅱ. 1. 너. 8) 및 표 5의 개정사항은 고시한 날부터 시 행한다.

## 3. article — PASS

- chunk_id: `4b2f1b9f022f5d8d:A014`
- source_path: `data/data_parsing/law/표시ㆍ광고의 공정화에 관한 법률 시행령.json`
- source_page: `None` / source_span: `제14조`
- 판정 근거: full text matches one source field
> 제14조(매출액이 없는 경우 등) 법 제9조제1항 단서에서 "대통령령으로 정하는 사업자등인 경우"란 사업자등이 다음 각 호의 어느 하나에 해당하는 경우를 말한다. <개정 2024.1.2>

## 4. article — PASS

- chunk_id: `bb51bc2a5017baec:PG003:S0016`
- source_path: `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/과거/식품등의 부당한 표시 또는 광고의 내용 기준_제2021-89호.json`
- source_page: `3` / source_span: `page 3, lines 33-35`
- 판정 근거: full text in OCR lines; start page matched
> 제3조(규제의 재검토) 식품의약품안전처장은「행정규제기본법」제8조 및 「훈령ㆍ예규 등의 발령 및 관리에 관한 규 정」에 따라 2020년 1월 1일을 기준으로 매 3년이 되는 시점(매 3년째의 12월 31일까지를 말한다)마다 그 타당성 을 검토하여 개선 등의 조치를 하여야 한다.

## 5. article — PASS

- chunk_id: `d7d6aa742889bf9d:PG003:S0013`
- source_path: `data/data_parsing/03_어린이 기호식품/법령_고시/과거/품질인증/어린이+기호식품+품질인증기준+전문(식약처+고시+제2023-58호).json`
- source_page: `3` / source_span: `page 3, lines 6-6`
- 판정 근거: full text in OCR lines; start page matched
> 제1조(시행일) 이 고시는 고시한 날부터 시행한다.

## 6. article — PASS

- chunk_id: `8beddd917de081dd:PG001:S0006`
- source_path: `data/data_parsing/03_어린이 기호식품/법령_고시/현재/품질인증/어린이 기호식품 품질인증기준(식품의약품안전처고시)(제2026-61호)(20260814).json`
- source_page: `1` / source_span: `page 1, lines 10-11`
- 판정 근거: full text in OCR lines; start page matched
> 제3조(품질인증 기준) ① 「어린이 식생활안전관리 특별법」 제14조에 따라 안전하고 영양을 고루 갖춘 어린이 기호 식품의 품질인증기준은 다음 각 호의 기준을 포함하여야 한다.

## 7. article — PASS

- chunk_id: `7d237411cc7cb62e:A008`
- source_path: `data/data_parsing/law/식품등의표시광고에관한법률_본문.json`
- source_page: `None` / source_span: `제8조`
- 판정 근거: full text matches one source field
> 제8조(부당한 표시 또는 광고행위의 금지)

## 8. article — PASS

- chunk_id: `db4a52405f29b6c2:A004`
- source_path: `data/data_parsing/law/친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률 시행령.json`
- source_page: `None` / source_span: `제4조`
- 판정 근거: full text matches one source field
> 제4조(과징금의 부과금액 등)

## 9. paragraph — PASS

- chunk_id: `0265d6e9e6e846f8:A040:P001`
- source_path: `data/data_parsing/law/건강기능식품에 관한 법률.json`
- source_page: `None` / source_span: `제40조 제1항`
- 판정 근거: full text matches one source field
> ① 식품의약품안전처장 또는 특별자치시장ㆍ특별자치도지사ㆍ시장ㆍ군수ㆍ구청장은 제5조제1항, 제6조제2항ㆍ제3항, 제23조 또는 제24조 등 중 어느 하나를 위반한 자를 관계 행정관청이나 수사기관에 신고하거나 고발한 자에게 1천만원의 범위에서 포상금을 지급할 수 있다. <개정 2015.2.3, 2018.3.13, 2024.1.2>

## 10. paragraph — PASS

- chunk_id: `61e69650dda6b19d:A004:P004`
- source_path: `data/data_parsing/law/표시·광고의 공정화에 관한 법률_본문.json`
- source_page: `None` / source_span: `제4조 제4항`
- 판정 근거: full text matches one source field
> ④ 관계 행정기관의 장은 통합공고 사항에 관한 법령이 제정되거나 개정된 경우에는 그 사항이 통합공고될 수 있도록 그 법령의 시행일 전에 공정거래위원회에 통보하여야 한다.

## 11. paragraph — PASS

- chunk_id: `a8849fd047eb965b:A019:P002:V003`
- source_path: `data/data_parsing/law/건강기능식품에 관한 법률 시행령.json`
- source_page: `None` / source_span: `제19조 제2항`
- 판정 근거: full text matches one source field
> ② 제1항에 따른 판매량은 위해 건강기능식품 등을 최초로 판매한 시점부터 적발시점까지의 출하량에서 회수량 및 반품ㆍ검사 등의 사유로 실제로 판매되지 아니한 양을 제외한 수량으로 하고, 판매가격은 판매기간 중 가격이 변동된 경우에는 판매시기별로 가격을 산정한다.

## 12. paragraph — PASS

- chunk_id: `7d237411cc7cb62e:A009:P007`
- source_path: `data/data_parsing/law/식품등의표시광고에관한법률_본문.json`
- source_page: `None` / source_span: `제9조 제7항`
- 판정 근거: full text matches one source field
> ⑦ 제1항부터 제4항까지의 규정에 따른 실증의 대상, 실증자료의 범위 및 요건, 제출방법 등에 관하여 필요한 사항은 총리령으로 정한다.

## 13. paragraph — PASS

- chunk_id: `7bef278a65d4e45a:A011:P006`
- source_path: `data/data_parsing/law/방문판매 등에 관한 법률 시행규칙.json`
- source_page: `None` / source_span: `제11조 제6항`
- 판정 근거: full text matches one source field
> ⑥ 제2항에 따라 다단계판매업 등록증 또는 후원방문판매업 등록증을 발급받은 자가 등록증을 분실하거나 등록증이 훼손된 경우 공정거래위원회 또는 시ㆍ도지사에게 별지 제3호의2서식의 등록증 재발급 신청서를 제출하여 등록증을 재발급받을 수 있다. 이 경우 등록증이 훼손되어 재발급을 신청하는 경우에는 기존 등록증을 첨부하여야 한다. <신설 2017.6.20>

## 14. paragraph — PASS

- chunk_id: `296150b7d07cdce2:A062:P002`
- source_path: `data/data_parsing/law/농림축산식품부 소관 친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률 시행규칙.json`
- source_page: `None` / source_span: `제62조 제2항`
- 판정 근거: full text matches one source field
> ② 제1항에 따른 유기농업자재 공시의 신청 시 제출되는 수입원료ㆍ재료의 사후관리에 필요한 사항은 국립농산물품질관리원장이 정하여 고시한다.

## 15. paragraph — PASS

- chunk_id: `c7db9cc3644c38da:A005:P004`
- source_path: `data/data_parsing/law/건강기능식품에 관한 법률 시행규칙.json`
- source_page: `None` / source_span: `제5조 제4항`
- 판정 근거: full text matches one source field
> ④지방식품의약품안전청장 또는 특별자치시장ㆍ특별자치도지사ㆍ시장ㆍ군수ㆍ구청장은 제3항에 따라 영업신고증을 발급한 후 별지 제10호서식의 영업신고관리대장을 작성ㆍ보관하거나 같은 서식으로 전산망에 입력하여 관리해야 한다. 이 경우 지방식품의약품안전청장 또는 특별자치시장ㆍ특별자치도지사ㆍ시장ㆍ군수ㆍ구청장은 반기별로 반기 종료 후 20일 이내에 별지 제11호서식의 영업신고관리 현황을 식품의약품안전처장에게

## 16. paragraph — PASS

- chunk_id: `2462dada5452960e:A021:P001:V002`
- source_path: `data/data_parsing/law/어린이 식생활안전관리 특별법.json`
- source_page: `None` / source_span: `제21조 제1항`
- 판정 근거: full text matches one source field
> ① 총리령으로 정하는 급식소를 운영하는 자는 어린이급식관리지원센터에 등록하여 위생 및 영양관리에 관한 지원을 받아야 한다. 다만, 급식소에 영양사를 두는 경우에는 등록을 하지 아니할 수 있다.

## 17. item — PASS

- chunk_id: `c7db9cc3644c38da:A009:P001:I002`
- source_path: `data/data_parsing/law/건강기능식품에 관한 법률 시행규칙.json`
- source_page: `None` / source_span: `제9조 제1항 제2호`
- 판정 근거: full text matches one source field
> 2. 원료 또는 성분의 함량

## 18. item — PASS

- chunk_id: `7bef278a65d4e45a:A003:I003`
- source_path: `data/data_parsing/law/방문판매 등에 관한 법률 시행규칙.json`
- source_page: `None` / source_span: `제3조 제3호`
- 판정 근거: full text matches one source field
> 3. 다른 소비자에 비하여 현저하게 유리한 조건으로 재화등을 판매ㆍ공급한다고 권유하여 소비자를 사업장에 방문하도록 하는 것

## 19. item — PASS

- chunk_id: `296150b7d07cdce2:A036:P001:I001`
- source_path: `data/data_parsing/law/농림축산식품부 소관 친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률 시행규칙.json`
- source_page: `None` / source_span: `제36조 제1항 제1호`
- 판정 근거: full text matches one source field
> 1. 인증기관 지정서

## 20. item — PASS

- chunk_id: `61e69650dda6b19d:A006:P003:I003`
- source_path: `data/data_parsing/law/표시·광고의 공정화에 관한 법률_본문.json`
- source_page: `None` / source_span: `제6조 제3항 제3호`
- 판정 근거: full text matches one source field
> 3. 그 밖에 위반행위의 시정을 위하여 필요한 조치

## 21. item — PASS

- chunk_id: `db4a52405f29b6c2:A007:P004:I029`
- source_path: `data/data_parsing/law/친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률 시행령.json`
- source_page: `None` / source_span: `제7조 제4항 제29호`
- 판정 근거: full text matches one source field
> 29. 법 제33조제2항 및 제3항(법 제34조제5항에서 준용하는 경우를 포함한다)에 따른 인증기관의 지위 승계 신고의 수리 및 신고수리 여부의 통지

## 22. item — PASS

- chunk_id: `df71ee26b065bf5b:A039:P003:I001`
- source_path: `data/data_parsing/law/친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률.json`
- source_page: `None` / source_span: `제39조 제3항 제1호`
- 판정 근거: full text matches one source field
> 1. 별표 11에 따른 인증심사원의 자격 기준을 갖추었음을 증명하는 서류

## 23. item — PASS

- chunk_id: `0265d6e9e6e846f8:A023:I006`
- source_path: `data/data_parsing/law/건강기능식품에 관한 법률.json`
- source_page: `None` / source_span: `제23조 제6호`
- 판정 근거: full text matches one source field
> 6. 수입이 금지된 것 또는 「수입식품안전관리 특별법」 제20조제1항에 따른 수입신고를 하지 아니하고 수입한 것

## 24. item — PASS

- chunk_id: `4b2f1b9f022f5d8d:A002:I002`
- source_path: `data/data_parsing/law/표시ㆍ광고의 공정화에 관한 법률 시행령.json`
- source_page: `None` / source_span: `제2조 제2호`
- 판정 근거: full text matches one source field
> 2. 인터넷 또는 PC통신

## 25. subitem — PASS

- chunk_id: `61e69650dda6b19d:A004:P001:I002:M003`
- source_path: `data/data_parsing/law/표시·광고의 공정화에 관한 법률_본문.json`
- source_page: `None` / source_span: `제4조 제1항 제2호 3목`
- 판정 근거: full text matches one source field
> 다. 그 밖에 소비자의 합리적인 선택을 현저히 그르칠 가능성이 있거나 공정한 거래질서를 현저히 해치는 경우

## 26. subitem — PASS

- chunk_id: `296150b7d07cdce2:A057:P001:I001:M001`
- source_path: `data/data_parsing/law/농림축산식품부 소관 친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률 시행규칙.json`
- source_page: `None` / source_span: `제57조 제1항 제1호 1목`
- 판정 근거: full text matches one source field
> 가. 무농약농산물을 생산하는 자

## 27. subitem — PASS

- chunk_id: `a8849fd047eb965b:A002:I001:M002`
- source_path: `data/data_parsing/law/건강기능식품에 관한 법률 시행령.json`
- source_page: `None` / source_span: `제2조 제1호 2목`
- 판정 근거: full text matches one source field
> 나. 건강기능식품벤처제조업 : 「벤처기업육성에 관한 특별법」 제2조에 따른 벤처기업이 건강기능식품을 가목의 건강기능식품전문제조업자에게 위탁하여 제조하는 영업

## 28. subitem — PASS

- chunk_id: `e106ae6d4dc75efa:A032:I001:M003`
- source_path: `data/data_parsing/law/방문판매 등에 관한 법률 시행령.json`
- source_page: `None` / source_span: `제32조 제1호 3목`
- 판정 근거: full text matches one source field
> 다. 해당 거래에 따른 대금결제와 직접 관련된 결제업자

## 29. appendix — PASS

- chunk_id: `426e03491e10c123:B003`
- source_path: `data/data_parsing/law/식품 등의 표시ㆍ광고에 관한 법률 시행령.json`
- source_page: `None` / source_span: `별표 3`
- 판정 근거: full text matches annex title and content in source order
> 과태료의 부과기준(제16조 관련) ■ 식품 등의 표시ㆍ광고에 관한 법률 시행령 [별표 3] <개정 2025. 9. 2.>                                                                                              과태료의 부과기준(제16조 관련)                                         

## 30. appendix — PASS

- chunk_id: `e106ae6d4dc75efa:B004`
- source_path: `data/data_parsing/law/방문판매 등에 관한 법률 시행령.json`
- source_page: `None` / source_span: `별표 4`
- 판정 근거: full text matches annex title and content in source order
> 과태료의 부과기준(제63조 관련) ■ 방문판매 등에 관한 법률 시행령 [별표 4] <개정 2021. 12. 28.>                                                                                        과태료의 부과기준(제63조 관련)                                                  

## 31. appendix — PASS

- chunk_id: `db4a52405f29b6c2:B001`
- source_path: `data/data_parsing/law/친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률 시행령.json`
- source_page: `None` / source_span: `별표 1`
- 판정 근거: full text matches annex title and content in source order
> 과징금의 부과금액 및 판매금액 산정의 세부기준(제4조제1항 관련) ■ 친환경농어업 육성 및 유기식품 등의 관리ㆍ지원에 관한 법률 시행령 [별표 1]     과징금의 부과금액 및 판매금액 산정의 세부기준(제4조제1항 관련)                                                                                                 

## 32. appendix — PASS

- chunk_id: `3190e5dbd6aefd6a:B018`
- source_path: `data/data_parsing/law/어린이 식생활안전관리 특별법 시행규칙.json`
- source_page: `None` / source_span: `별표 18`
- 판정 근거: full text matches annex title and content in source order
> 어린이급식관리지원센터의 급식소 등록신청서 ■ 어린이 식생활안전관리 특별법 시행규칙 [별지 제10호서식] <신설 2021. 12. 3.>                                                                                                                        어린이급식관리지원센터의 급식소 등록신청서   

## 33. table — PASS

- chunk_id: `DOC_표시·광고의 공정화에 관한 법:B001:R004`
- source_path: `data/data_parsing/law/표시·광고의 공정화에 관한 법률 위반사업자등에 대한 과징금부과 세부기준 등에 관한 고시.json`
- source_page: `None` / source_span: `별표 (원본 별표번호 0000) / 원본 줄 5-5`
- 판정 근거: table row matches consecutive annex source lines
>  나. 중대성 정도에 따른 부과기준율 또는 부과기준금액은 위반행위별 세부평가기준표의 평가에 의하여 산정된 점수에 비례하여 정할 수 있다. 

## 34. table — PASS

- chunk_id: `bc579008458506dd:B002:R010`
- source_path: `data/data_parsing/law/식품등의 부당한 표시 또는 광고의 내용 기준.json`
- source_page: `None` / source_span: `별표 2 / 원본 줄 24-25`
- 판정 근거: table row matches consecutive annex source lines
> ├───┼─────────────────────┼────────────────┤ │냉장  │0∼10℃ 이하로 온도를 낮추어 보존하는 것  │-                               │

## 35. guide — PASS

- chunk_id: `cbfc8683ba236d34:PG008:S0019`
- source_path: `data/data_parsing/00_공통_표시광고-20261123T025100Z-1-001/현재/★++「식품등의+부당한+표시+또는+광고의+내용+기준」+고시+전문(제2025-79호,+2025.12.4.json`
- source_page: `8` / source_span: `page 8, lines 1-50`
- 판정 근거: full text in OCR lines; start page matched
> 품유형과 용도를 명확하게 표시한 경우 마약류로 더 마약류 관리에 법률 에서 분류되어 식품등 포함되면 성분테트라히드로칸나비놀 칸나비디올 에 아니되는 천연적으로 성분의 등임에도 온[ㄷ는 존재하는 명칭이나 을 나타내는 표시광고 다른 다른 업체의 제품을 업체나 비방하는 표시 또는 운 다른 제품을 비방하거나 비방하는 가 업소의 것으로 의심되는표 시광고 [YI "다른 이 0와 고를

## 36. guide — PASS

- chunk_id: `5840bab5b8cfa0a8:PG005:S0025`
- source_path: `data/data_parsing/02_일반식품/법령_고시/시행예정/2028/표시기준/식품등의 표시기준(식품의약품안전처고시)(제2026-37호)(20280101).json`
- source_page: `5` / source_span: `page 5, lines 23-24`
- 판정 근거: full text in OCR lines; start page matched
> 2) 「식품위생법 시행령」 제21조제1호에 따른 식품제조ㆍ가공업의 영업자가 즉석섭취식품을 제조ㆍ가공하여 급식 용 도로 집단급식소에 납품 판매하는 경우 표시사항은 서류로 제공할 수 있다.

## 37. guide — PASS

- chunk_id: `d7d6aa742889bf9d:PG006:S0028`
- source_path: `data/data_parsing/03_어린이 기호식품/법령_고시/과거/품질인증/어린이+기호식품+품질인증기준+전문(식약처+고시+제2023-58호).json`
- source_page: `6` / source_span: `page 6, lines 7-9`
- 판정 근거: full text in OCR lines; start page matched
> 2) 수입식품의 경우에는 「수입식품안전관리 특별법」 제7조에 따른 우수수 입업소에서 수입한 식품이어야 한다. 나. 조리식품

## 38. guide — PASS

- chunk_id: `f32c7bd98edadb61:PG096:S0317`
- source_path: `data/data_parsing/해설서, 사례/20210225_식품등_부당한_광고_판단기준_가이드라인(판단안내서)_수정.json`
- source_page: `96` / source_span: `page 96, lines 1-3`
- 판정 근거: full text in OCR lines; start page matched
> 전자상거래 등에서의 03 소비자보호에 관한 법률

## 39. guide — PASS

- chunk_id: `c0790727b050c22d:PG001:S0003`
- source_path: `data/data_parsing/01_건강기능식품/원본 데이터/기능성원료-20261123T031711Z-1-001/원료별정보/개별인정원료/1104295_건강기능식품 기능성 원료 소비자 리포트_마키베리추출물(제2025-8호).txt`
- source_page: `1` / source_span: `page 1, lines 12-13`
- 판정 근거: full text matches one source field
> 기능성 원료명 인정번호( )  · 마키베리추출물 제 호( 2025-8 )

## 40. guide — PASS

- chunk_id: `0e0f9e9b95fbbcd2:PG001:S0005`
- source_path: `data/data_parsing/01_건강기능식품/원본 데이터/기능성원료-20261123T031711Z-1-001/원료별정보/개별인정원료/1108064_제2025-63호 건강기능식품 기능성 원료 소비자 리포트_콘드로이친황산염.txt`
- source_page: `1` / source_span: `page 1, lines 13-21`
- 판정 근거: full text matches one source field
> 일일 섭취량 · 콘드로이친황산염으로서 일  1,200 mg/ 섭취 시  주의사항 영 유아 어린이 임산부 및 수유부는 섭취를 피할 것 · · , ,  특정질환 알레르기 체질 등 이 있는 분은 섭취에 주의할 것 · ( ) 이상사례 발생 시 섭취를 중단하고 전문가와 상담할 것 ·   · 수술 전후 또는 항응고제 항혈소판제 비스테로이드계 항염증약 , ,  복용자는 섭취 전 전문의와 상담할 것 천식이

## 41. case — PASS

- chunk_id: `fc1959b68d6d1e90:PG022:S0055`
- source_path: `data/data_parsing/해설서, 사례/20220406_온라인_식품·건강기능식품·의약외품·화장품_분야_부당광고_사례집-웹게시용(표지수정).json`
- source_page: `22` / source_span: `page 22, lines 3-43`
- 판정 근거: full text in OCR lines; start page matched
> 사례집 식품 건강기능식품 화장품 윤음喜 '체중감소약 식품등을 식욕억제제' 등으로 광고 자연 식욕억제제 릉몰深 '식욕억제제' 등으로 려운 뚱뚱한가열기 :상품상세참조 원산지 식욕 뚱뚱한가열기 억제제 체중감량 릉 균일가 체중감소 남성용 유 취침/야간 등 야간 60캡슐 해외직구 제품을 '체중감소약' 등으로 광고 노배송비 1개당9900원 미국에서배송 20

## 42. case — PASS

- chunk_id: `fdb75433e5ba9e14:PG051:S0116`
- source_path: `data/data_parsing/해설서, 사례/합본_식품_등_온라인_부당광고_사례집.json`
- source_page: `51` / source_span: `page 51, lines 1-15`
- 판정 근거: full text in OCR lines; start page matched
> [위반사례] ○ 식품 등을 가공할 때 사용한 원재료나 성분이 원료나 성분의 효능·효과를 제품의 효능·효과로 오인·혼동 ▶ ‘글루타치온’의 효능·효과 표방 ▶ ‘타우린’의 효능·효과 표방 ▶ ‘민들레’의 효능·효과 표방 ▶ ‘링곤베리’, ‘비오틴’, ‘차가버섯’의 효능·효과 표방 ▶ ‘흰강낭콩추추물’, ‘차가 버섯추출물’, ‘토마토농축 분말’, ‘뽕나무잎추출물’의 효능·효과 표방 - 45 -

## 43. case — PASS

- chunk_id: `e25157ee2a78cbf1:R002860`
- source_path: `data/data_parsing/해설서, 사례/식품관련법 위반사례_식품안전나라.json`
- source_page: `None` / source_span: `record 2860`
- 판정 근거: record object matches parsed source
> {"PRCSCITYPOINT_BSSHNM": "연SG스크린골프", "INDUTY_CD_NM": "일반음식점", "LCNS_NO": "20170628030", "DSPS_DCSNDT": "20251230", "DSPS_BGNDT": "20260202", "DSPS_ENDDT": "-", "DSPS_TYPECD_NM": "영업소폐쇄", "VILTCN": "(20251118)영업정지 처분 기간 중

## 44. case — PASS

- chunk_id: `e25157ee2a78cbf1:R003528`
- source_path: `data/data_parsing/해설서, 사례/식품관련법 위반사례_식품안전나라.json`
- source_page: `None` / source_span: `record 3528`
- 판정 근거: record object matches parsed source
> {"PRCSCITYPOINT_BSSHNM": "32불록까페(BLOCKCAFE)", "INDUTY_CD_NM": "일반음식점", "LCNS_NO": "20200249311", "DSPS_DCSNDT": "20260325", "DSPS_BGNDT": "20260331", "DSPS_ENDDT": "-", "DSPS_TYPECD_NM": "영업소폐쇄", "VILTCN": "(20260114)시설물

## 45. case — PASS

- chunk_id: `e25157ee2a78cbf1:R001170`
- source_path: `data/data_parsing/해설서, 사례/식품관련법 위반사례_식품안전나라.json`
- source_page: `None` / source_span: `record 1170`
- 판정 근거: record object matches parsed source
> {"PRCSCITYPOINT_BSSHNM": "최가네축산", "INDUTY_CD_NM": "식육즉석판매가공업", "LCNS_NO": "20220268087", "DSPS_DCSNDT": "20250421", "DSPS_BGNDT": "-", "DSPS_ENDDT": "-", "DSPS_TYPECD_NM": "영업허가·등록취소", "VILTCN": "(20250421)타. 법 제24조제2항을 

## 46. case — PASS

- chunk_id: `e25157ee2a78cbf1:R004393`
- source_path: `data/data_parsing/해설서, 사례/식품관련법 위반사례_식품안전나라.json`
- source_page: `None` / source_span: `record 4393`
- 판정 근거: record object matches parsed source
> {"PRCSCITYPOINT_BSSHNM": "오방가르드(ovantgarde)", "INDUTY_CD_NM": "일반음식점", "LCNS_NO": "19960137099", "DSPS_DCSNDT": "20260825", "DSPS_BGNDT": "20260826", "DSPS_ENDDT": "20261024", "DSPS_TYPECD_NM": "영업정지", "VILTCN": "(202608

## 47. record — PASS

- chunk_id: `3422fc7d2d8aad23:R000432`
- source_path: `data/data_parsing/01_건강기능식품/원본 데이터/개별인정-20261123T031709Z-1-001/건강기능식품_개별인정형_정보.json`
- source_page: `None` / source_span: `record 432`
- 판정 근거: record object matches parsed source
> {"WT_UNIT": "mg/일", "PRIMARY_FNCLTY": "(국문) 노화로 인해 감소될 수 있는 근력 유지에 도움을 줄 수 있음\n(영문) May help to maintain muscle strength which can be affected by aging", "IFTKN_ATNT_MATR_CN": "(1) 영유아, 어린이, 임산부 및 수유부는 섭취를 피할 것\n(2) 특정질환

## 48. record — PASS

- chunk_id: `ef4b83ea4a5a8f68:R000428`
- source_path: `data/data_parsing/01_건강기능식품/원본 데이터/품목분류-20261123T031718Z-1-001/건강기능식품_품목분류정보.json`
- source_page: `None` / source_span: `record 428`
- 판정 근거: record object matches parsed source
> {"LCLAS_NM": "건강기능식품", "SCLAS_CD": "701060000", "HELT_ITM_GRP_NM": "비타민/루테인", "MLSFC_NM": "영양소", "SCLAS_NM": "혼합기능성원료", "HELT_ITM_GRP_CD": "701060023", "LCLAS_CD": "700000000", "MLSFC_CD": "701000000"}

## 49. record — PASS

- chunk_id: `3e85ebc3edc60881:R0000771`
- source_path: `data/data_parsing/02_일반식품/원본 데이터/식품원료/food_raw_material.jsonl`
- source_page: `None` / source_span: `record 771`
- 판정 근거: record object matches source JSONL line
> {"LCLAS_NM":"식품원료(A코드)","MLSFC_NM":"식물","RPRSNT_RAWMTRL_NM":"고추씨앗기름파우더","RAWMTRL_NCKNM":" ","ENG_NM":"Hot pepper, Cayenne, Capsicum, Chili Pepper, Red Pepper, Tabasco","SCNM":"Capsicum annuum L. / Capsicum frutescens var

## 50. record — PASS

- chunk_id: `3e85ebc3edc60881:R0012697`
- source_path: `data/data_parsing/02_일반식품/원본 데이터/식품원료/food_raw_material.jsonl`
- source_page: `None` / source_span: `record 12697`
- 판정 근거: record object matches source JSONL line
> {"LCLAS_NM":"식품원료(A코드)","MLSFC_NM":"수산물","RPRSNT_RAWMTRL_NM":"Bengal tongue sole","RAWMTRL_NCKNM":null,"ENG_NM":null,"SCNM":"Cynoglossus cynoglossus","REGN_CD_NM":"-","RAWMTRL_STATS_CD_NM":null,"USE_CND_NM":null}
