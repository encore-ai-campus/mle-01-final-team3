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

## Vercel 연결

저장소에서 Vercel 프로젝트를 연결할 때 다음 설정을 사용합니다.

- Root Directory: `front`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

`vercel.json`은 React Router의 직접 진입(`/reviews/:reviewId` 등)이 `index.html`로 전달되도록 SPA rewrite를 제공합니다.

Vercel Project Settings의 Environment Variables에는 환경별로 다음 공개 설정만 추가합니다.

```text
VITE_API_BASE_URL=<검증된 API base URL>
VITE_USE_FIXTURES=false
```

`VITE_*` 값은 브라우저 번들에 노출되므로 API 키, DB 비밀번호, 세션 비밀값을 넣으면 안 됩니다. 실제 Vercel 프로젝트 생성·Git 저장소 연결·환경변수 입력은 계정 권한이 필요한 외부 작업이므로 이 저장소에서는 설정 파일과 배포 문서까지만 준비했습니다.

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
- PDF 저장 URL 또는 다운로드 응답 방식
- 비밀번호 정책과 변경 완료 후 알림 처리
