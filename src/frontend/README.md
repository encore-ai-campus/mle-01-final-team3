# 식품 광고 심의 프런트엔드

React 19, TypeScript, Vite, Vitest 기반의 식품 광고 문구 심의 시연 화면입니다. 현재는 기존 fixture Provider와 API Provider를 함께 유지하며, 백엔드 계약이 확정된 기능부터 단계적으로 연결할 수 있도록 구성되어 있습니다.

## 로컬 실행

```powershell
npm.cmd install
npm.cmd run dev
```

## 데이터 제공 모드

### Fixture 모드

목업 데이터와 화면 흐름을 확인할 때 사용합니다. 백엔드가 없어도 전체 시연 흐름을 실행할 수 있습니다.

```powershell
$env:VITE_USE_FIXTURES = "true"
npm.cmd run dev
```

시나리오는 URL의 `scenario` 파라미터로 선택할 수 있습니다. 예: `/reviews?scenario=LG-10`.

### API 모드

공개 API 기본 주소가 정해진 뒤 다음 환경 변수를 설정합니다.

```text
VITE_USE_FIXTURES=false
VITE_API_BASE_URL=https://api.example.com
```

`VITE_API_BASE_URL`이 비어 있으면 API Provider는 실제 요청을 보내지 않고 `not-configured` 상태를 반환합니다. API 주소, 인증 방식, 엔드포인트가 확정되기 전에는 fixture 모드를 유지합니다.

읽기 전용 검토 목록 contract는 `createRestApiContract`에 확정된 목록 경로를 주입하는 방식으로 연결합니다. 경로 기본값을 소스에 넣지 않으므로 백엔드 명세가 확정되기 전에는 이 contract가 자동으로 활성화되지 않습니다.

`VITE_*` 변수에는 비밀번호, 세션 비밀값, DB 접속 정보를 넣지 않습니다. 브라우저에 공개되는 값은 API의 공개 주소뿐입니다.

## 주요 화면 경로

- `/`: 대시보드
- `/checks/new`: 광고 문구 검사 입력
- `/checks/:checkId`: 검사 결과 및 추천 문구
- `/reviews`: 검토함 목록
- `/reviews/:reviewId`: 문서 상세 및 업무 보고서
- `/reviews/:reviewId/reports/:reportStage`: 보고서 상세
- `/employees`, `/employees/new`, `/employees/:employeeId`: 직원 목록·등록·수정

## Vercel 배포 설정

- Root Directory: `src/frontend`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

React Router 직접 진입을 지원하려면 저장소의 `vercel.json` rewrite 설정을 함께 사용합니다. 백엔드 API가 준비되기 전에는 Vercel 환경 변수 `VITE_USE_FIXTURES=true`로 시연 모드를 유지합니다.

## 검증 명령

```powershell
npm.cmd test -- --run
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

## 아직 확정이 필요한 API 항목

- 현재 로그인 사용자 조회 경로(`/api/v1/me`)
- 운영 API 주소와 Vercel 도메인 허용 CORS 설정
- 파일 첨부 업로드 응답 형식
- 로그인 계정 및 비밀번호 발급·초기화 절차
- 각 업무 기능의 최종 HTTP 메서드와 경로
