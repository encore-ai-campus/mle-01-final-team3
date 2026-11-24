# 식품 광고 심의 후속조치·게시 검증 프론트 설계

## 의도

목업 이미지 모음의 화면과 상태 흐름을 React + TypeScript 기반의 직원용 프론트로 구현한다. 사용자는 광고 문구를 검사하고, AI 판정 근거를 검토하며, 역할별 후속조치와 업무 흐름을 확인한다.

현재 대상 저장소의 `front`는 비어 있고, React/TypeScript 설정·라우터·공통 컴포넌트·API 클라이언트·백엔드 엔드포인트·공유 타입은 확인되지 않았다. 따라서 기존 프론트 구현을 재사용할 수 없으며, 프론트 최소 기반을 새로 구성해야 한다. 저장소의 현재 실행 기반은 Python 3.12와 `uv` 중심이며, 프론트 스택은 아직 존재하지 않는다.

## 목표

- 목업의 공통 레이아웃과 기본 페이지 템플릿을 실제 라우트로 구성하고, 아트보드별 상태를 상호작용 사례로 반영한다.
- 반복 UI를 공통 컴포넌트와 타입으로 분리한다.
- 실제 API 연동을 위한 명시적 타입 경계를 만들고, 확인되지 않은 엔드포인트는 추측하지 않는다.
- API가 없거나 설정되지 않은 경우 로딩·빈 데이터·오류 상태를 사용자에게 분명히 보여 준다.
- 개발용 fixture는 별도 provider로만 주입하고, 기본 실행은 실제 API provider를 사용한다.
- 접근성, 모바일 반응형, TypeScript 검사, 린트, 빌드를 검증한다.

## 비목표

- 현재 확인되지 않은 백엔드 API·인증·권한 모델·DB 스키마를 임의로 설계하거나 구현하지 않는다.
- 목업의 숫자·이름·날짜·광고 문구를 제품 데이터로 하드코딩하지 않는다.
- AI 판정, 법률 판단, 그래프 검색, 파일 추출 엔진을 프론트에서 재구현하지 않는다.
- 서버가 제공하지 않는 저장·승인·배정 동작을 성공한 것처럼 처리하지 않는다.

## 제약과 확인된 사실

- 작업 폴더: `C:/Users/Playdata/Desktop/김동석/최종프로젝트/mle-01-final-team3/front`
- 현재 `front` 폴더는 비어 있다.
- 저장소에는 현재 React/TypeScript package manifest가 없다.
- 현재 저장소에서 API 라우트, 응답 타입, 인증 방식, 백엔드 서버를 확인하지 못했다.
- 로컬에는 직원용 화면 이미지 8개와 정보 구조 이미지 1개가 `0김동석/project/UI/직원용 화면 설계_이미지`에 있다. 이 8개는 별도 정적 목업 세트다.
- Artifact URL은 브라우저에서 확인했으며, 전체 아트보드는 **41개**다. 아티팩트 상단에는 **5 pages**로 표시되고, 같은 페이지의 필터·모달·성공·오류·권한·빈 상태가 여러 아트보드로 분리되어 있다.
- 따라서 구현 범위는 “8개 화면”이 아니라, 아티팩트의 5개 기본 페이지 템플릿과 41개 상태/상호작용 사례를 추적하는 것으로 정정한다.

## 접근 방식

### 1. API 우선형

실제 API를 기본 데이터 공급자로 두고, API 계약이 확인되지 않은 화면은 빈 상태·설정 안내·오류 상태를 표시한다. 데이터 구조와 동작을 추측하지 않는 장점이 있지만, API 계약 전에는 목업의 예시 데이터가 표시되지 않는다.

### 2. 데모 데이터 분리형

개발용 fixture provider를 실제 API provider와 분리하고, `VITE_USE_FIXTURES=true`처럼 명시적으로 켠 경우에만 목업 흐름을 재현한다. 시각 검증은 가능하지만 데모 모드가 운영 환경에 켜지지 않도록 기본값과 표기를 엄격히 분리해야 한다.

### 선택

1번을 기본으로 하고 2번을 개발용 보조 경로로 채택한다. 이 조합은 실제 API 원칙을 지키면서도 API 계약이 도착하기 전 공통 UI·라우팅·반응형을 검증할 수 있다. fixture는 제품 데이터가 아니라 테스트/시각 검증 전용이며, 운영 기본값으로 사용하지 않는다.

## 화면 범위와 라우트 제안

아티팩트의 41개 아트보드는 41개 라우트로 만들지 않는다. 실제 라우트 단위는 기본 페이지 템플릿으로 묶고, 각 아트보드는 화면 상태·쿼리 필터·모달·오류·알림·권한 변형으로 테스트한다.

현재 확인된 기본 페이지 템플릿은 다음과 같다.

- 법무 담당자 대시보드
- 검토함
- 검토 보고서 상세
- 마이페이지/계정 메뉴
- 알림 패널/알림 상태

대표 상태 사례에는 검토함 빈 상태, 검토 대기·검토 중·오늘 처리 완료 필터, 담당자/판정 필터, 검토 적합·부적합 완료, 적합/부적합 확인 모달, 부적합 사유 입력·검증, 저장 실패, PDF 저장 완료, 다른 담당자 검토 중 비활성, 판단 보류 흐름, 새 알림·알림 없음·첫 로그인 알림이 포함된다. 이 범위는 아티팩트의 41개 아트보드에서 확인된 사례이며, 목업의 예시 데이터 자체를 운영 데이터로 하드코딩한다는 뜻은 아니다.

기존 라우터가 없으므로 아래 경로를 제안한다. 백엔드 API 경로와 혼동되지 않도록 UI 라우트로만 사용하며, 승인 후 구현 전에 팀의 라우트 규칙이 발견되면 그 규칙을 우선한다.

| 목업 화면 | 제안 UI 라우트 | 핵심 목적 |
| --- | --- | --- |
| 대시보드 | `/` | 접수 현황·할 일·최근 보고서 확인 |
| 검토함 | `/reviews` | 보고서 검색·AI 판정/처리 상태/담당자/처리일 필터링 |
| 검토 보고서 상세 | `/reviews/:reviewId` | 보고서 확인·적합/부적합 처리·사유 입력·PDF 저장 |
| 마이페이지/계정 메뉴 | `/account` | 계정 정보·비밀번호 변경·로그아웃 |
| 알림 패널 | `/notifications` 또는 오버레이 | 새 알림·지난 알림·알림 없음 상태 확인 |

로컬의 별도 8개 직원용 목업(홈·광고 문구 검사·검사 결과·진행 상황·검토함·검토 상세·매뉴얼 추출·업무 흐름 관리)은 이번 Artifact 범위와 섞지 않는다. 해당 8개까지 함께 구현할지는 Artifact 41개 상태 구현 후 별도 범위로 확정한다.

## 수정·생성할 파일

`front`가 비어 있으므로 승인 후 다음 구조를 생성한다. 실제 파일명은 초기화 결과와 팀 규칙에 따라 조정할 수 있다.

- `front/package.json`, `front/tsconfig*.json`, `front/vite.config.ts`, `front/index.html`
- `front/src/main.tsx`, `front/src/App.tsx`, `front/src/routes.tsx`
- `front/src/styles/tokens.css`, `front/src/styles/globals.css`
- `front/src/components/layout/AppShell.tsx`, `Sidebar.tsx`, `PageHeader.tsx`
- `front/src/components/ui/Button.tsx`, `Badge.tsx`, `Card.tsx`, `DataTable.tsx`, `StateView.tsx`, `ProgressStepper.tsx`
- `front/src/components/domain/AdSummaryCard.tsx`, `FindingCard.tsx`, `ReviewTaskRow.tsx`, `EvidencePanel.tsx`, `WorkflowGraph.tsx`, `ManualRelationTable.tsx`
- `front/src/pages/DashboardPage.tsx`, `ReviewsPage.tsx`, `ReviewDetailPage.tsx`, `AccountPage.tsx`, `NotificationsPanel.tsx`
- 별도 범위로 확정될 때 `CheckFormPage.tsx`, `CheckResultPage.tsx`, `ProgressPage.tsx`, `ManualExtractionPage.tsx`, `WorkflowPage.tsx`를 추가한다.
- `front/src/types/domain.ts`, `front/src/types/api.ts`
- `front/src/api/client.ts`, `front/src/api/contract.ts`, `front/src/api/providers.ts`
- `front/src/hooks/useAsyncResource.ts`, `front/src/hooks/useMutation.ts`
- `front/src/test/` 또는 현재 선택한 테스트 디렉터리
- `front/.env.example`, 필요 시 `front/README.md`

API가 확인될 때까지 `api/contract.ts`에는 확인된 계약만 추가하고, 미확인 요청은 TODO와 사용자-facing 설정 상태로 남긴다.

## 컴포넌트 구성

### 공통 레이아웃

- `AppShell`: 좌측 사이드바와 콘텐츠 영역을 감싼다.
- `Sidebar`: 역할별 메뉴를 표시하고 현재 라우트를 강조한다.
- `PageHeader`: 제목·설명·breadcrumb·주요 액션을 제공한다.
- `Card`, `Button`, `Badge`, `DataTable`: 목업 전반의 카드·버튼·상태 색상·표를 통일한다.
- `StateView`: loading, empty, error, not-configured 상태를 공통 표현한다.

### 도메인 UI

- 대시보드: `SummaryCard`, `TaskList`, `RecentReportTable`, `NotificationList`
- 검토함: `ReviewFilterBar`, `ReviewTaskTable`, `ReviewStatusBadge`, `EmptyReviewState`
- 검토 상세: `ReportMeta`, `ReviewDecisionForm`, `DecisionConfirmDialog`, `RejectReasonDialog`, `PdfAction`
- 계정/알림: `AccountMenu`, `AccountForm`, `NotificationPanel`, `NotificationEmptyState`
- 별도 범위: `CheckForm`, `FindingList`, `ProgressStepper`, `UploadDropzone`, `WorkflowGraph`

시각적 그래프는 새 그래프 라이브러리를 도입하지 않고, 우선 CSS/SVG 기반의 제한된 단계 그래프로 구현한다. 드래그 편집이나 대규모 그래프가 API 요구사항으로 확인될 때만 라이브러리 도입을 재검토한다.

## TypeScript 타입

API가 제공하는 실제 스키마를 우선하되, 화면 책임에 필요한 최소 도메인 타입을 다음처럼 분리한다.

- `UserRole`, `Department`, `ProductType`, `AdChannel`
- `Ad`, `AdDraft`, `AdStatus`, `AdSummary`
- `CheckRequest`, `CheckStatus`, `CheckResult`
- `FindingSeverity`, `FindingKind`, `Finding`, `EvidenceReference`, `AlternativeCopy`
- `ReviewTask`, `ReviewStatus`, `ReviewDecision`, `ReviewDetail`
- `WorkflowStep`, `WorkflowCondition`, `WorkflowEdge`, `WorkflowDefinition`
- `ManualDocument`, `ExtractionJob`, `ExtractedRelation`, `DepartmentConfirmation`
- `DashboardSummary`, `Notification`, `ActivityLogEntry`
- `ApiError`, `ApiResponse<T>`, `PaginatedResponse<T>`

`any`는 사용하지 않는다. API가 불명확한 영역은 `unknown`으로 받고 런타임 파서/검증을 거쳐 도메인 타입으로 좁힌다.

## API와 화면 데이터 연결

### 기본 원칙

- 기본 provider는 `VITE_API_BASE_URL`을 사용한다.
- 엔드포인트 경로·HTTP method·request/response 필드는 실제 백엔드 명세 또는 실행 확인 후에만 작성한다.
- 인증 토큰·비밀값은 코드나 `sessionStorage`에 저장하지 않는다. 인증 방식 확인 전에는 로그인/토큰 처리를 구현하지 않는다.
- 서버의 저장·승인·검토 요청이 성공 응답을 준 경우에만 화면 상태를 갱신한다.
- API 응답은 `unknown`으로 수신한 뒤 타입 가드/스키마 검증을 거친다.

### Provider 구조

- `ApiProvider`: 실제 fetch 기반. API base URL 미설정 시 `not-configured`를 반환한다.
- `FixtureProvider`: 개발 전용. 명시적 환경 변수로만 선택되며 화면에 `데모 데이터` 표시를 둔다.
- `DataProvider` 인터페이스: 페이지는 provider 구현체가 아니라 인터페이스를 사용한다.

현재 확인할 내용:

- 각 화면에 대응하는 API URL과 method
- 인증 및 사용자 역할 전달 방식
- 광고/검사/검토/매뉴얼/워크플로우 ID와 페이지네이션 규칙
- 검사 요청의 비동기 상태 조회 또는 SSE/WebSocket 여부
- 승인·수정 요청·부서 확인·단계 수정의 저장 응답 형식

위 항목은 백엔드 담당자가 API 명세를 제공하기 전까지 확인되지 않은 상태로 표시한다.

## 버튼과 사용자 동작

- 홈의 `새 광고 문구 검사`: `/checks/new` 이동
- 홈의 `수정하기`·`검사하기`: 해당 광고/초안의 검사 화면 이동
- 검사 폼의 `임시 저장`: API 계약이 확인된 경우에만 저장 mutation 실행
- 검사 폼의 `자동 검사 시작`: 검사 요청 후 결과 라우트로 이동하거나 비동기 진행 상태 표시
- 결과의 문장 선택: 우측 근거·대안 패널 갱신
- 결과의 `적용`: 폼 초안에 대안 문구 반영. 서버 저장 여부는 API 계약에 따른다.
- 결과의 `검토 요청 보내기`: 담당 부서 배정 요청. 성공 전까지 중복 제출 방지
- 진행 상황의 `담당자에게 문의`: 실제 메시징 API가 없으면 비활성화 또는 확인 필요 상태
- 검토함의 필터 탭: 서버 필터 파라미터가 확인되면 query string과 연결
- 검토 상세의 `맞음/다름`: 판정 피드백 mutation. 성공 전에는 선택 상태만 로컬 임시 표시
- 검토 상세의 `법무팀에 넘기기`·`수정 요청`·`승인`: 서버가 제공하는 명확한 transition만 연결
- 매뉴얼의 파일 업로드: 허용 확장자·크기·업로드 API가 확인된 후 연결
- 업무 흐름의 `매뉴얼 다시 추출`·`단계 추가`·`조건 수정`: 저장 API가 확인되기 전에는 설정 안내 또는 비활성 상태

## 로딩·빈 데이터·오류 상태

- 로딩: 카드/표의 skeleton과 작업 중인 버튼 상태를 제공한다.
- 빈 데이터: “표시할 검토 건이 없습니다”처럼 역할·필터를 포함한 설명과 다음 행동을 제공한다.
- API 미설정: base URL 또는 계약이 없음을 안내하고 데모 모드 여부를 구분한다.
- 오류: 상태 코드·서버 원문을 그대로 노출하지 않고, 재시도·뒤로가기·문의 행동을 제공한다.
- mutation 오류: 입력값을 보존하고 중복 제출을 막은 뒤 오류를 해당 영역에 표시한다.
- 권한 오류: 서버 응답에 따라 접근 제한 상태를 표시하며, 프론트에서 역할을 임의로 상승시키지 않는다.

## 모바일 반응형

- 데스크톱 목업의 고정 사이드바는 모바일에서 접이식 상단/드로어 메뉴로 변환한다.
- 3열 요약 카드는 단일 열 또는 2열로 축소한다.
- 표는 우선순위 열을 남기고 나머지는 가로 스크롤 또는 카드형으로 제공한다.
- 검사 결과의 좌우 패널은 모바일에서 세로 흐름으로 전환하고, 선택한 문장 근거를 바로 아래에 표시한다.
- 업무 흐름 그래프는 가로 스크롤 가능한 캔버스 또는 단계 목록으로 대체한다.
- 터치 대상 최소 크기, 키보드 포커스, 명확한 상태 색상과 텍스트 라벨을 보장한다.

## 검증 방법

승인 후 다음 순서로 검증한다.

1. `npm install` 또는 팀이 선택한 패키지 매니저로 의존성 설치
2. `npm run typecheck`로 TypeScript 검사
3. `npm run lint`로 린트 검사
4. `npm run build`로 프로덕션 빌드
5. 실제 API base URL 미설정 상태에서 5개 기본 라우트의 not-configured/empty 상태 확인
6. 개발용 fixture 모드에서 5개 기본 라우트와 아티팩트 41개 상태 사례(필터·모달·성공·오류·권한·알림)를 확인
7. 데스크톱과 모바일 viewport에서 사이드바·표·패널·그래프 반응형 확인
8. 키보드만으로 메뉴·폼·필터·검토 결정 컨트롤을 조작하고 포커스 표시 확인
9. API가 제공되면 실제 응답·오류·권한·비동기 검사 흐름을 fixture와 비교

## 남은 확인 사항

구현 전에 다음 정보를 확인해야 한다.

- 백엔드 서버의 실행 명령과 기본 URL
- 인증/로그인 방식과 현재 사용자 역할 응답
- 위 8개 화면에 필요한 API 명세 또는 OpenAPI 문서
- 파일 업로드·검사 비동기 처리·승인/수정 요청의 상태 전이
- 프론트에 사용할 팀 표준 패키지 매니저와 Node.js 버전
- 운영에서 fixture 모드를 허용하지 않을지에 대한 배포 설정

이 정보가 없으면 해당 동작은 추측 구현하지 않고 확인 필요 상태로 남긴다.

