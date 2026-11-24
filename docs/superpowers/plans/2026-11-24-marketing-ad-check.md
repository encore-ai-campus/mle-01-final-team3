# Marketing Ad Check and Report Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the missing marketing ad-copy inspection menu and connect the mockup's input, result, progress, and reviewer report flow without guessing an API contract.

**Architecture:** Keep the existing React Router, shared shell/components, and legal review routes. Add a separate typed `CheckDataProvider` boundary with an API provider that returns `not-configured` until a verified backend contract exists, plus a fixture provider for visual flow tests. Enrich the existing review detail with finding/evidence presentation and local feedback controls.

**Tech Stack:** React 19, TypeScript, React Router 7, Vite, Vitest, Testing Library, existing CSS tokens and components.

**Spec:** `docs/superpowers/specs/2026-11-24-marketing-ad-check-design.md`

## Global Constraints

- Preserve the current React + TypeScript and Vite setup.
- Reuse existing `AppShell`, `Sidebar`, `PageHeader`, `Card`, `Button`, `StateView`, and CSS tokens.
- Do not invent API endpoints, HTTP methods, auth fields, or server success states.
- Default production behavior must remain API-first and show an explicit not-configured state when no verified contract exists.
- Fixture behavior is opt-in through the existing `VITE_USE_FIXTURES=true` path and must not become the production default.
- Do not hardcode mockup values as production data; fixture values are isolated to the fixture provider.
- Avoid `any`; parse external payloads from `unknown` with type guards.
- Keep mobile layout single-column and preserve accessible labels, alerts, and status announcements.

## Review Focus

- Direct navigation to `/checks/new`, `/checks/:checkId`, and `/progress/:checkId` must render the intended page instead of 404.
  - Test in the route test and fixture flow test.
- API mode must not pretend that a check was saved or completed when the contract is absent.
  - Test `ApiCheckProvider` returns `not-configured` for load, save, and start operations.
- Required ad name and copy validation must block submission while preserving entered values.
  - Test the form with empty required fields and assert the alert and preserved input values.
- Findings with no evidence or no alternatives must render a clear empty explanation rather than blank cards.
  - Test the result page with empty arrays.
- Reviewer feedback must be keyboard accessible and remain local-only until a verified mutation contract exists.
  - Test `맞음`/`다름` state and the not-configured submission behavior.

### Task 1: Add typed check domain and provider boundary

**Files:**
- Modify: `front/src/types/domain.ts`
- Modify: `front/src/types/api.ts`
- Create: `front/src/api/checkProvider.ts`
- Create: `front/src/api/checkFixtureProvider.ts`
- Create: `front/src/api/checkProvider.test.ts`

**Interfaces:**
- Produces `CheckInput`, `CheckResult`, `CheckFinding`, `CheckProgress`, `CheckDataProvider`, and `createCheckProvider(scenarioId)` for pages and routes.
- `CheckDataProvider` exposes `getResult(checkId)`, `saveDraft(input)`, `startCheck(input)`, and `getProgress(checkId)` returning typed `DataState` values.

- [x] **Step 1: Write failing provider tests** for API-mode not-configured states and fixture-mode result/progress data.
- [x] **Step 2: Run the focused provider test and confirm the expected missing-module failure.**
- [x] **Step 3: Implement the domain types and providers with runtime-safe `unknown` parsing and isolated fixture data.**
- [x] **Step 4: Run the focused test and confirm it passes.**
- [x] **Step 5: Commit with `feat(front): add typed ad check provider`.**

### Task 2: Build the ad-check input, result, and progress pages

**Files:**
- Create: `front/src/components/domain/AdCheckForm.tsx`
- Create: `front/src/components/domain/FindingList.tsx`
- Create: `front/src/components/domain/EvidenceCard.tsx`
- Create: `front/src/components/domain/CheckProgressStepper.tsx`
- Create: `front/src/pages/CheckFormPage.tsx`
- Create: `front/src/pages/CheckResultPage.tsx`
- Create: `front/src/pages/ProgressPage.tsx`
- Create: `front/src/pages/CheckFormPage.test.tsx`
- Create: `front/src/pages/CheckResultPage.test.tsx`
- Create: `front/src/pages/ProgressPage.test.tsx`

**Interfaces:**
- Consumes `CheckDataProvider` from Task 1 and existing UI primitives.
- Produces accessible form, result, and progress screens with links to `/reviews` and `/reviews/:reviewId`.

- [x] **Step 1: Write failing tests** for required-field validation, fixture submit navigation, finding/evidence rendering, empty evidence, and progress rendering.
- [x] **Step 2: Run the three focused test files and confirm the expected missing-module/render failures.**
- [x] **Step 3: Implement the minimal components and pages, keeping API mode not-configured and fixture mode navigable.**
- [x] **Step 4: Run the focused tests and confirm they pass.**
- [x] **Step 5: Commit with `feat(front): add ad check result and progress pages`.**

### Task 3: Connect navigation and enrich reviewer report details

**Files:**
- Modify: `front/src/App.tsx`
- Modify: `front/src/components/layout/Sidebar.tsx`
- Modify: `front/src/pages/DashboardPage.tsx`
- Modify: `front/src/pages/ReviewDetailPage.tsx`
- Create: `front/src/components/domain/ReviewEvidencePanel.tsx`
- Create: `front/src/components/domain/ReviewFeedbackControls.tsx`
- Modify: `front/src/components/layout/AppShell.test.tsx`
- Modify: `front/src/App.routes.test.tsx`
- Create: `front/src/pages/ReviewDetailEvidence.test.tsx`

**Interfaces:**
- Consumes Task 1 check types and Task 2 page routes.
- Produces sidebar links for `광고 문구 검사` and `진행 상황`, dashboard entry link, all check routes, and report detail evidence/feedback UI.

- [x] **Step 1: Write failing navigation and report tests** for menu hrefs, direct route rendering, dashboard entry, finding evidence, and keyboard feedback controls.
- [x] **Step 2: Run focused navigation/report tests and confirm they fail before the route/menu/report changes.**
- [x] **Step 3: Add routes and links, then add the report evidence and local feedback components without inventing server mutations.**
- [x] **Step 4: Run focused tests and confirm they pass.**
- [x] **Step 5: Commit with `feat(front): connect ad check and reviewer report flow`.**

### Task 4: Full verification and visual route audit

**Files:**
- Modify: `front/README.md` if route/setup documentation needs updating.
- Modify: `docs/superpowers/specs/2026-11-24-marketing-ad-check-design.md` only if verification reveals a scope correction.

- [x] **Step 1: Run the full `npm test` suite and read the complete result.**
- [x] **Step 2: Run `npm run typecheck`, `npm run lint`, and `npm run build`.**
- [x] **Step 3: Run the app in fixture mode and manually verify `/checks/new` → `/checks/:checkId` → `/progress/:checkId` → `/reviews/:reviewId`, including mobile-width layout and keyboard labels.**
- [x] **Step 4: Verify API mode behavior through `ApiCheckProvider` tests: no successful check is claimed without a contract.**
- [x] **Step 5: Update route and API contract documentation.**

