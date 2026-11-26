# Food Guard Frontend

식품 광고 심의 후속조치 및 게시 검증 화면입니다. Claude Artifact의 41개 아트보드를 5개 라우트 템플릿과 상태 시나리오로 구성했습니다.

## 실행

```powershell
npm.cmd install
npm.cmd run dev
```

검증된 API 계약이 아직 연결되지 않은 기본 모드에서는 API 요청을 추측하지 않고 각 화면에 `API 연결 설정이 필요합니다` 상태를 표시합니다.

### Fixture 모드

Fixture는 시각·상호작용 검증 전용이며 production 기본값이 아닙니다.

```powershell
$env:VITE_USE_FIXTURES = "true"
npm.cmd run dev
```

아트보드 상태는 `?scenario=LG-1`부터 `?scenario=LG-41`까지 선택할 수 있습니다. 예: `/reviews?scenario=LG-10`.

현재 시연 배포 주소는 [foodad-audit.vercel.app](https://foodad-audit.vercel.app)이며, 화면과 버튼은 fixture 기반 가상 데이터로 동작합니다. 가상 데이터는 실제 업무 데이터가 아닙니다.

시연 흐름 예시:

- `/checks/new?demo=true`: 광고 문구 검사 입력 → 검사 결과 → 1차·2차 보고서
- `/?demo=true`: 가상 대시보드
- `/reviews?demo=true&scenario=LG-5`: 검토 대기 목록
- `/reviews/fixture-review-3?demo=true&team=legal`: 법무팀 검토 및 승인·반려 시연
- `/employees?demo=true&role=admin`: 관리자 직원관리 시연

### 광고 문구 검사 경로

- `/checks/new`: 광고명·제품 유형·원료·게시 채널·광고 문구 입력
- `/checks/:checkId`: 위반 의심·애매·안전 결과와 근거·대안 문구 확인
- `/progress` 또는 `/progress/:checkId`: 자동 검사와 담당자 검토 진행 상황 확인
- `/reviews` 및 `/reviews/:reviewId`: 검토함과 검토 보고서, AI 근거·피드백 확인
- `/reviews/:reviewId/reports/:reportStage`: 1차·2차·법무팀 참조 보고서 상세
- `/workflow`: 관리자 업무 흐름 시각화
- `/employees`, `/employees/new`, `/employees/:employeeId`: 관리자 직원 목록·등록·수정·삭제

광고 검사 API 계약이 확인되지 않은 상태에서도 기본 화면은 fixture 기반으로 동작합니다. 실제 API를 확인한 뒤에만 `VITE_USE_FIXTURES=false`로 전환합니다.

## Vercel 연결

현재 Vercel 프로젝트 `foodad-audit`은 API가 준비되기 전 시연을 위해 production 환경에서 fixture 모드로 배포합니다. 저장소에서 Vercel 프로젝트를 연결할 때 다음 설정을 사용합니다.

- Root Directory: `src/frontend`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

`vercel.json`은 React Router의 직접 진입(`/reviews/:reviewId` 등)이 `index.html`로 전달되도록 SPA rewrite를 제공합니다.

Vercel Project Settings의 Environment Variables에는 시연 배포에 다음 공개 설정을 추가합니다.

```text
VITE_USE_FIXTURES=true
```

실제 API 계약이 확인되면 `VITE_USE_FIXTURES=false`로 바꾸고, 확인된 `VITE_API_BASE_URL`만 추가합니다. 로컬에서 `?demo=true`를 붙이면 환경변수와 무관하게 같은 시연 모드를 확인할 수 있습니다.

`VITE_*` 값은 브라우저 번들에 노출되므로 API 키, DB 비밀번호, 세션 비밀값을 넣으면 안 됩니다.

## 품질 검사

```powershell
npm.cmd test -- --run
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

## API 계약 확인 필요 사항

현재 `ApiProvider`는 semantic operation을 주입받도록만 구현되어 있으며, 실제 endpoint를 임의로 만들지 않습니다. 백엔드 연결 전에 다음을 확정해야 합니다.

- 대시보드, 검토 목록·상세, 판정 저장, 계정, 비밀번호 변경, 알림 목록·읽음 처리의 실제 HTTP 메서드와 경로
- 인증 방식, 권한 오류 형식, 세션 만료 처리
- 각 요청·응답의 필드와 날짜 형식
- 판정 저장의 중복 요청·동시 담당자 처리 규칙
- 광고 검사 시작·임시 저장·결과·진행 상황 조회의 실제 HTTP 메서드와 경로
- 광고 검사 요청·finding·근거·대안 문구·진행 단계 응답 필드와 권한 규칙
- PDF 저장 URL 또는 다운로드 응답 방식
- 비밀번호 정책과 변경 완료 후 알림 처리
