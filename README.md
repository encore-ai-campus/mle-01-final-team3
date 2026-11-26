# mle-01-final-team3
식품 광고 심의 후속조치 및 게시 검증 AI 에이전트
# PDF -> JSON 변환

`건강기능식품/기능성원료/원료별 정보/개별인정` 폴더 아래의 PDF를 재귀적으로 읽어 PDF 하나당 JSON 하나를 생성합니다. JSON에는 원본 파일 정보와 페이지별 텍스트 및 표가 들어갑니다.

```bash
uv sync
python scripts/pdf_to_json.py
```

기본 실행은 입력 폴더 안에 PDF와 동일한 상대 경로로 `.json` 파일을 생성합니다. 다른 폴더를 사용하거나 출력 위치를 분리하려면 다음처럼 실행합니다.

```bash
python scripts/pdf_to_json.py --input-dir "건강기능식품/기능성원료/원료별 정보/개별인정" --output-dir data_parsing/json
```

스캔본처럼 텍스트 레이어가 없는 PDF는 OCR이 필요하므로 이 스크립트만으로 텍스트가 추출되지 않을 수 있습니다.
