# 식품 광고 심의 프론트 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Claude Artifact reference as a typed React + TypeScript frontend with five route-level page templates and all 41 artboard states represented as explicit interaction and fixture scenarios.

**Architecture:** Build a small Vite React application in `front` with a shared shell, route pages, typed domain models, and a provider boundary. `ApiProvider` must remain non-guessing until the backend contract is supplied; `FixtureProvider` is an explicit development-only path for visual and interaction verification. The 41 artboards are state cases of five page templates, not 41 routes.

**Tech Stack:** React, TypeScript, Vite, React Router, plain CSS files, native `fetch`, Vitest, React Testing Library, and npm scripts. Do not add a UI kit or graph library unless a later verified requirement requires it.

**Spec:** `docs/superpowers/specs/2026-11-24-food-ad-review-front-design.md`

## Global Constraints

- Work only in `C:/Users/Playdata/Desktop/김동석/최종프로젝트/mle-01-final-team3/front` for product code.
- Preserve the existing Python 3.12/`uv` backend project; do not replace its configuration.
- Do not invent API URLs, HTTP methods, request fields, response fields, authentication behavior, or status transitions.
- Use real API data by default. If `VITE_API_BASE_URL` or the verified API contract is missing, render an explicit not-configured/empty/error state.
- Fixture data is development-only, opt-in, and visibly labeled; it must not become the production default.
- Do not hardcode mock counts, names, dates, advertising copy, or other example values in production components.
- Do not use `any`; unknown API payloads must be narrowed before entering domain components.
- Keep parsing, data access/provider code, route pages, shared UI, and domain components separate.
- Keep Vercel deployment compatible: the Vercel project root is `front`, the Vite build output is `dist`, and client-side deep links use an explicit SPA rewrite to `/index.html`.
- Expose only non-secret browser configuration through `VITE_*` variables. Never place API keys, database credentials, or server-only secrets in Vite environment files or client code.
- Use `st.session_state` only if Streamlit code is later touched; this React task must not add a parallel Streamlit UI.
- Every mutation must preserve input on failure, prevent duplicate submission, and update visible state only after a confirmed success response.
- Verify TypeScript, lint, build, responsive layout, keyboard access, loading, empty, error, permission, and not-configured states.

## Review Focus

- Missing API contract or base URL: pages must render not-configured state without guessing a request.
- Unknown or malformed API payload: provider must return a typed error rather than crash a route.
- Duplicate review decision submission: controls must disable while pending and preserve the result on failure.
- Review ownership/permission mismatch: non-owners may view and export but cannot decide.
- Mobile and keyboard use of tables, dialogs, filters, and notification panels: all controls need usable focus order and visible state.

---

### Task 1: Bootstrap the frontend workspace and quality gates

**Files:**
- Create: `front/package.json`
- Create: `front/tsconfig.json`, `front/tsconfig.node.json`
- Create: `front/vite.config.ts`, `front/index.html`
- Create: `front/eslint.config.js`, `front/.gitignore`, `front/.env.example`
- Create: `front/vercel.json`
- Create: `front/src/main.tsx`, `front/src/App.tsx`
- Create: `front/src/styles/tokens.css`, `front/src/styles/globals.css`
- Test: `front/src/app.test.tsx`

**Interfaces:**
- Produces npm scripts: `dev`, `typecheck`, `lint`, `test`, `build`.
- Produces `App` as the root React component and `main.tsx` as the browser entry point.
- Produces CSS variables for the reference palette, spacing, radii, typography, focus ring, and semantic status colors.
- Produces a Vercel-compatible static SPA deployment configuration for the `front` project root.

- [ ] **Step 1: Write the failing smoke test**

  Add `renders the app root` and assert the root renders a stable accessible landmark such as `main` and a temporary loading/not-configured message.

- [ ] **Step 2: Run the test to verify it fails**

  Run from `front`: `npm test -- --run src/app.test.tsx`.
  Expected: FAIL because the frontend package and root component do not exist.

- [ ] **Step 3: Create the minimal Vite React TypeScript scaffold**

  Use the current project’s available Node/npm environment. Add only the packages required for React, routing, TypeScript, linting, and tests. Keep scripts deterministic and make `npm run build` produce a static bundle.

- [ ] **Step 4: Implement the root mount and design tokens**

  Render `<App />` from `main.tsx`, define global box sizing and focus styles, and add the blue/gray/red/amber/green semantic tokens observed in the reference without copying example data.

- [ ] **Step 5: Run the smoke test and quality gates**

  Run `npm test -- --run src/app.test.tsx`, `npm run typecheck`, `npm run lint`, and `npm run build`.
  Expected: all commands pass.

- [ ] **Step 6: Add the Vercel SPA deployment boundary**

  Add `vercel.json` with the official Vite SPA rewrite from every request to `/index.html`; keep build and output settings aligned with the Vercel project settings (`npm run build`, `dist`, root directory `front`). Add only safe `VITE_API_BASE_URL` and `VITE_USE_FIXTURES` placeholders to `.env.example` and document that actual environment values are configured in Vercel per environment.

- [ ] **Step 7: Commit the scaffold**

  Commit only frontend scaffolding and configuration with message `chore(front): bootstrap typed react app`.

### Task 2: Define typed domain contracts and provider boundaries

**Files:**
- Create: `front/src/types/domain.ts`
- Create: `front/src/types/api.ts`
- Create: `front/src/api/errors.ts`
- Create: `front/src/api/client.ts`
- Create: `front/src/api/provider.ts`
- Create: `front/src/api/apiProvider.ts`
- Create: `front/src/api/fixtureProvider.ts`
- Create: `front/src/api/providerFactory.ts`
- Create: `front/src/fixtures/artifactScenarios.ts`
- Test: `front/src/api/provider.test.ts`

**Interfaces:**
- `type DataState<T> = { status: "loading" } | { status: "ready"; data: T } | { status: "empty"; message: string } | { status: "error"; error: ApiError } | { status: "not-configured"; message: string }`.
- `interface DataProvider` exposes semantic methods: `getDashboard()`, `listReviews(query)`, `getReviewDetail(reviewId)`, `submitDecision(input)`, `getAccount()`, `updatePassword(input)`, `listNotifications()`, `markNotificationsRead()`.
- `ApiProvider` accepts a typed `ApiContract`/configuration object and must return `not-configured` when no verified contract is supplied; it must not construct guessed paths.
- `FixtureProvider` implements the same interface and accepts a named `ArtifactScenarioId` for the 41 reference cases.
- `ReviewQuery` supports only verified UI filters: search, AI judgment, processing status, assignee, and processing date.

- [ ] **Step 1: Write provider contract tests**

  Test that missing API configuration returns `not-configured`, malformed JSON returns `error`, fixture selection returns the requested scenario, and mutation failure leaves the submitted reason available to the caller.

- [ ] **Step 2: Run the provider tests to verify they fail**

  Run `npm test -- --run src/api/provider.test.ts`.
  Expected: FAIL because types and providers do not exist.

- [ ] **Step 3: Implement domain and API types**

  Define `UserRole`, `Department`, `ReviewJudgment`, `ReviewStatus`, `ReviewTask`, `ReviewDetail`, `DashboardSummary`, `Notification`, `Account`, `DecisionInput`, `ApiError`, and `DataState` with discriminated unions. Keep IDs and timestamps typed as strings until the backend contract says otherwise.

- [ ] **Step 4: Implement the provider boundary without endpoint guesses**

  Implement `ApiProvider` around a typed client that requires an injected contract. Until the contract is supplied, each method returns `not-configured`. Parse external payloads from `unknown` and map non-2xx/network/parse failures to `ApiError`.

- [ ] **Step 5: Implement the opt-in fixture provider and 41 scenario registry**

  Store scenarios in a dedicated fixture module with explicit `DEMO ONLY` labeling. The registry must cover LG-1 through LG-41 as listed in Task 8, including data-state differences and interaction preconditions. Components must never import this registry directly.

- [ ] **Step 6: Run provider tests and quality gates**

  Run `npm test -- --run src/api/provider.test.ts`, `npm run typecheck`, and `npm run lint`.
  Expected: PASS with no `any` usage.

- [ ] **Step 7: Commit the provider boundary**

  Commit with message `feat(front): add typed data providers`.

### Task 3: Build the shared shell and accessible UI primitives

**Files:**
- Create: `front/src/components/layout/AppShell.tsx`
- Create: `front/src/components/layout/Sidebar.tsx`
- Create: `front/src/components/layout/PageHeader.tsx`
- Create: `front/src/components/ui/Button.tsx`, `Badge.tsx`, `Card.tsx`, `DataTable.tsx`, `Dialog.tsx`, `Select.tsx`, `TextField.tsx`, `StateView.tsx`, `ToastRegion.tsx`
- Create: `front/src/hooks/useDataState.ts`, `useMutationState.ts`
- Test: `front/src/components/layout/AppShell.test.tsx`, `front/src/components/ui/Dialog.test.tsx`

**Interfaces:**
- `AppShell({ children, currentPath, user, onNavigate })` renders the responsive navigation and main landmark.
- `StateView({ state, onRetry })` renders loading, empty, error, and not-configured variants.
- `Dialog({ open, title, description, children, onClose })` uses a native accessible dialog pattern with focus return.
- `DataTable<T>({ rows, columns, getRowKey, emptyState })` supports keyboard-visible row actions and mobile overflow.

- [ ] **Step 1: Write failing shell and dialog tests**

  Assert navigation labels, current-route indication, mobile menu button semantics, dialog focusable controls, Escape close, and focus return after close.

- [ ] **Step 2: Run tests to verify they fail**

  Run `npm test -- --run src/components/layout/AppShell.test.tsx src/components/ui/Dialog.test.tsx`.
  Expected: FAIL because components do not exist.

- [ ] **Step 3: Implement the shell and primitives**

  Reuse the reference’s sidebar/content structure and status colors. Keep navigation data-driven and avoid page-specific business logic inside primitives.

- [ ] **Step 4: Add responsive behavior**

  Collapse the sidebar into a drawer on narrow viewports, make tables horizontally scrollable or card-like, and preserve focus order.

- [ ] **Step 5: Run component tests and build**

  Run the targeted tests, `npm run typecheck`, `npm run lint`, and `npm run build`.
  Expected: PASS.

- [ ] **Step 6: Commit shared UI**

  Commit with message `feat(front): add accessible app shell primitives`.

### Task 4: Implement dashboard and notification states

**Files:**
- Create: `front/src/pages/DashboardPage.tsx`
- Create: `front/src/components/domain/SummaryCard.tsx`, `TaskList.tsx`, `RecentReportTable.tsx`
- Create: `front/src/components/domain/NotificationPanel.tsx`, `NotificationEmptyState.tsx`
- Modify: `front/src/App.tsx`
- Test: `front/src/pages/DashboardPage.test.tsx`, `front/src/components/domain/NotificationPanel.test.tsx`

**Interfaces:**
- `DashboardPage({ provider })` consumes `DataProvider.getDashboard()` and renders summary, tasks, recent reports, and the notification entry point.
- `NotificationPanel({ state, onMarkAllRead, onClose })` renders new, historical, and empty notification states.

- [ ] **Step 1: Write failing dashboard tests**

  Cover ready, empty, loading, error, and not-configured dashboard states; task navigation; and notification open/close/read actions.

- [ ] **Step 2: Implement the dashboard page and notification panel**

  Map only provider data to UI. Do not embed the Artifact’s sample counts or names in the page.

- [ ] **Step 3: Add route wiring for `/` and `/notifications`**

  Use the app’s router and provider factory; keep notification panel usable as an overlay while retaining `/notifications` as a direct state route when needed.

- [ ] **Step 4: Run tests and verify the relevant artboards**

  Run the targeted tests and verify LG-1, LG-2, and LG-3 in fixture mode.

- [ ] **Step 5: Commit dashboard work**

  Commit with message `feat(front): add dashboard and notifications`.

### Task 5: Implement the review inbox and filter states

**Files:**
- Create: `front/src/pages/ReviewsPage.tsx`
- Create: `front/src/components/domain/ReviewFilterBar.tsx`, `ReviewTaskTable.tsx`, `ReviewStatusBadge.tsx`, `EmptyReviewState.tsx`
- Modify: `front/src/App.tsx`
- Test: `front/src/pages/ReviewsPage.test.tsx`

**Interfaces:**
- `ReviewsPage({ provider, searchParams })` calls `listReviews(ReviewQuery)` and synchronizes verified filters with URL query parameters.
- `ReviewFilterBar({ value, options, onChange })` exposes search, AI judgment, processing status, assignee, and processing-date controls.
- `ReviewTaskTable` renders view actions and ownership/read-only state without deciding permission locally.

- [ ] **Step 1: Write failing filter and state tests**

  Assert query-string synchronization, filtered results, empty results, loading, API error, and view navigation. Include the “another reviewer is processing” read-only presentation.

- [ ] **Step 2: Implement filter state and table**

  Keep filter names aligned with `ReviewQuery`; do not add guessed backend parameters. Use client-side filtering only in fixture mode.

- [ ] **Step 3: Add `/reviews` route**

  Preserve filter state on refresh and back navigation.

- [ ] **Step 4: Run tests and verify the relevant artboards**

  Run the targeted tests and verify LG-5, LG-6, LG-7, LG-8, LG-9, LG-10, LG-11, LG-14, LG-21, LG-25, and LG-28 in fixture mode.

- [ ] **Step 5: Commit the inbox**

  Commit with message `feat(front): add review inbox filters`.

### Task 6: Implement review detail, decisions, dialogs, and error recovery

**Files:**
- Create: `front/src/pages/ReviewDetailPage.tsx`
- Create: `front/src/components/domain/ReportMeta.tsx`, `ReviewDecisionForm.tsx`, `DecisionConfirmDialog.tsx`, `RejectReasonDialog.tsx`, `PdfAction.tsx`, `ReadOnlyDecisionNotice.tsx`
- Modify: `front/src/App.tsx`
- Test: `front/src/pages/ReviewDetailPage.test.tsx`, `front/src/components/domain/ReviewDecisionForm.test.tsx`

**Interfaces:**
- `ReviewDetailPage({ reviewId, provider })` calls `getReviewDetail(reviewId)` and owns only route-level pending/error state.
- `ReviewDecisionForm({ detail, onSubmit })` emits `DecisionInput = { reviewId, decision: "approved" | "rejected"; reason?: string }`.
- `RejectReasonDialog` requires a non-empty reason before calling `onSubmit`.
- `DecisionConfirmDialog` requires explicit confirmation and disables repeated submits.
- `PdfAction` calls only a verified provider capability; if absent, it renders unavailable/not-configured state.

- [ ] **Step 1: Write failing detail and mutation tests**

  Cover ready/loading/error/not-configured detail, approve confirmation, reject reason validation, filled reason preservation after failure, read-only decision controls, PDF unavailable, and successful status update.

- [ ] **Step 2: Implement detail components and mutation flow**

  Use provider mutation results as the only source of confirmed status changes. Keep the form state intact on failure and show an inline error/toast.

- [ ] **Step 3: Add `/reviews/:reviewId` route**

  Return to `/reviews` after a confirmed success only when the provider reports success; otherwise remain on detail.

- [ ] **Step 4: Run tests and verify the relevant artboards**

  Run targeted tests and verify LG-12, LG-13, LG-15, LG-16, LG-17, LG-18, LG-19, LG-20, LG-22, LG-23, LG-24, LG-26, LG-27, LG-29, LG-30, LG-31, LG-32, LG-33, and LG-34 in fixture mode.

- [ ] **Step 5: Commit review detail**

  Commit with message `feat(front): add review detail decisions`.

### Task 7: Implement account and route-level state integration

**Files:**
- Create: `front/src/pages/AccountPage.tsx`
- Create: `front/src/components/domain/AccountMenu.tsx`, `AccountForm.tsx`
- Modify: `front/src/App.tsx`, `front/src/components/layout/Sidebar.tsx`
- Test: `front/src/pages/AccountPage.test.tsx`, `front/src/App.routes.test.tsx`

**Interfaces:**
- `AccountPage({ provider })` calls `getAccount()` and `updatePassword(input)`.
- `AccountForm` validates the local password rules only when specified by the verified API/auth contract; otherwise it exposes server validation errors without inventing policy.
- The router maps `/account` and direct notification states while preserving unknown-route not-found behavior.

- [ ] **Step 1: Write failing account and route tests**

  Cover account loading/error/not-configured, successful save, failed save with preserved input, route navigation, unknown route, and sidebar account menu behavior.

- [ ] **Step 2: Implement the account page and menu**

  Keep passwords out of global state and logs. Do not implement authentication persistence without a confirmed auth contract.

- [ ] **Step 3: Run tests and verify LG-4, LG-38, LG-39, and LG-40**

  Verify account menu, password form, save success, first-login alert, and password-change notice in fixture mode.

- [ ] **Step 4: Commit account integration**

  Commit with message `feat(front): add account and route states`.

### Task 8: Lock the 41-artboard coverage matrix

**Files:**
- Create: `front/src/fixtures/artboardMatrix.ts`
- Create: `front/src/test/artboardCoverage.test.ts`
- Modify: `front/src/fixtures/artifactScenarios.ts`
- Modify: `front/src/pages/*.tsx` only where a missing state is found

**Interfaces:**
- `ArtboardCase` contains `id: "LG-1" | ... | "LG-41"`, `route`, `scenario`, `expectedState`, and `expectedInteraction`.
- `artboardMatrix` contains exactly 41 unique IDs and maps each to one of the five route-level templates.

- [ ] **Step 1: Encode the 41-artboard matrix**

  Register the exact route mapping: `/` → LG-1, LG-2, LG-3; `/reviews` → LG-5, LG-6, LG-7, LG-8, LG-9, LG-10, LG-11, LG-14, LG-21, LG-25, LG-28; `/reviews/:reviewId` → LG-12, LG-13, LG-15, LG-16, LG-17, LG-18, LG-19, LG-20, LG-22, LG-23, LG-24, LG-26, LG-27, LG-29, LG-30, LG-31, LG-32, LG-33, LG-34; `/account` → LG-4, LG-38, LG-39, LG-40; `/notifications` → LG-35, LG-36, LG-37, LG-41. This list must contain each of LG-1 through LG-41 exactly once.

- [ ] **Step 2: Write the coverage test**

  Assert that the matrix has exactly 41 unique artboard IDs, every case has a valid route and expected state, and every state has a fixture provider scenario.

- [ ] **Step 3: Run the coverage test**

  Run `npm test -- --run src/test/artboardCoverage.test.ts`.
  Expected: PASS with 41 cases.

- [ ] **Step 4: Verify fixture navigation manually**

  Start with `VITE_USE_FIXTURES=true npm run dev`, traverse the five routes, and confirm that each artboard case can be reached through the documented filter, dialog, notification, or mutation flow.

- [ ] **Step 5: Commit the coverage matrix**

  Commit with message `test(front): cover artifact artboards`.

### Task 9: Final responsive, accessibility, and release verification

**Files:**
- Modify: `front/src/styles/*.css`, affected components/pages only after verification
- Create: `front/README.md`
- Test: `front/src/accessibility.test.tsx` or the chosen existing accessibility test location

**Interfaces:**
- `front/README.md` documents Node/npm prerequisites, `npm` commands, `VITE_API_BASE_URL`, fixture opt-in, and the API contract blocker without exposing secrets.

- [ ] **Step 1: Add failing accessibility assertions for the final gaps**

  Assert one main landmark, labelled navigation, labelled dialogs, keyboard-operable filters/actions, visible focus, and no unlabeled icon-only action in the tested routes.

- [ ] **Step 2: Fix responsive and accessibility issues**

  Verify narrow viewport behavior for sidebar, tables, report detail panels, dialogs, and notification overlays. Use text labels in addition to color for status.

- [ ] **Step 3: Run the full verification suite**

  Run `npm test -- --run`, `npm run typecheck`, `npm run lint`, and `npm run build`.
  Expected: all commands pass with no warnings treated as errors.

- [ ] **Step 4: Run the not-configured verification**

  Start without `VITE_API_BASE_URL` and without fixture mode. Confirm that no guessed network calls are made and that all five routes render explicit not-configured/empty states.

- [ ] **Step 5: Run the fixture verification**

  Start with the explicit fixture flag and verify all 41 matrix cases, including mobile and keyboard flows.

- [ ] **Step 6: Document remaining API questions**

  Record exact missing endpoints, auth behavior, payload schemas, async check status mechanism, PDF behavior, and state-transition rules in `front/README.md`.

- [ ] **Step 7: Commit final verification changes**

  Commit with message `chore(front): verify responsive states and document setup`.

