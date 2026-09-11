# PRISM Web UI Implementation Plan

> **For agentic workers:** This plan is executed inline in the current session. Steps use checkbox syntax for tracking.

**Goal:** Build a responsive React/TypeScript product interface over the accepted PRISM FastAPI APIs.

**Architecture:** Add a Vite frontend with a centralized typed API client and reusable status/presentation components. Keep the backend as the analytical source of truth; backend changes, if any, are limited to CORS/static transport integration.

**Tech Stack:** React, TypeScript, Vite, React Router, Vitest, Testing Library, CSS.

**Spec:** `docs/superpowers/specs/2026-09-10-prism-web-ui-design.md`

## Global Constraints

- Do not modify accepted analytical semantics or analytics services.
- Do not read, print, modify, or commit `.env`.
- Do not expose credentials in frontend source or bundled environment files.
- Centralize HTTP access and type transport responses to the actual Pydantic schemas.
- Client-side logic may display and filter returned categorical values only.
- Do not commit automatically.

---

### Task 1: Frontend scaffold and API contracts

**Files:** Create `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/types/api.ts`, `frontend/src/lib/api.ts`, and `frontend/src/lib/api.test.ts`.

**Interfaces:** `api.ts` exports transport types for projects, history, forecast/confidence/risk/decision support, summaries, and upload responses. `api.ts` exports `PrismApi` methods for each consumed endpoint. Tests cover URL construction, successful JSON decoding, and normalized API errors.

- [ ] Write failing API-client tests before implementation.
- [ ] Implement the Vite scaffold and exact transport types from `app/schemas/project_data.py` and `app/schemas/api.py`.
- [ ] Run `npm test -- --run src/lib/api.test.ts` and verify it passes.
- [ ] Run `npm run build` and verify the scaffold compiles.

### Task 2: Application shell and shared states

**Files:** Create `frontend/src/App.tsx`, `frontend/src/styles.css`, `frontend/src/components/AppShell.tsx`, `frontend/src/components/StatusBadge.tsx`, `frontend/src/components/StatePanel.tsx`, `frontend/src/components/MetricCard.tsx`, and component tests.

**Interfaces:** `AppShell` renders navigation and outlet content. `StatusBadge` maps backend categorical values to readable labels and accessible styles. `StatePanel` renders loading, empty, error, or unavailable states.

- [ ] Write failing component tests for labels, loading/error states, and responsive shell landmarks.
- [ ] Implement shared components without deriving analytical values.
- [ ] Verify the component tests and build.

### Task 3: Projects and project dashboard

**Files:** Create `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/ProjectDashboardPage.tsx`, `frontend/src/components/ProjectSummary.tsx`, `frontend/src/components/ActivityTable.tsx`, and tests.

**Interfaces:** Projects page calls `getProjects`. Dashboard calls `getProjectPredictiveSummary`; activity rows use the returned `activities_requiring_attention` and `activities_with_insufficient_evidence` plus categorical fields from the summary. No frontend aggregation is introduced.

- [ ] Write failing page tests for project loading, dashboard summary display, attention/insufficient-evidence copy, and backend 404 handling.
- [ ] Implement route pages, project navigation, table filters based only on returned categorical fields, and accessible empty states.
- [ ] Verify page tests and build.

### Task 4: Activity detail and historical evidence

**Files:** Create `frontend/src/pages/ActivityDetailPage.tsx`, `frontend/src/components/ForecastCard.tsx`, `frontend/src/components/EvidenceQualityCard.tsx`, `frontend/src/components/RiskCard.tsx`, `frontend/src/components/DecisionSupportCard.tsx`, `frontend/src/components/ProgressHistory.tsx`, and tests.

**Interfaces:** Activity detail calls `getActivityPredictiveSummary` and `getActivityHistory`; optional observed endpoint calls are isolated behind client methods. Cards display backend values verbatim, including insufficient/unavailable states. History visualization plots only returned dated snapshots and does not calculate forecast lines.

- [ ] Write failing tests for available, insufficient, unavailable, missing optional fields, and unknown-activity states.
- [ ] Implement detail layout and evidence language distinguishing observed history, forecast, evidence quality, predictive risk, and bounded decision support.
- [ ] Verify tests and build.

### Task 5: Upload workflow and refresh

**Files:** Create `frontend/src/pages/ReportsPage.tsx`, `frontend/src/components/UploadPanel.tsx`, and tests; modify `frontend/src/lib/api.ts` only for upload progress/error decoding if needed.

**Interfaces:** Upload uses `POST /api/v1/upload` with `FormData`. Accepted extensions and max size are displayed from the backend configuration contract already present in `app/core/config.py`; extraction remains server-side. Success refreshes project data through navigation or an explicit refresh action.

- [ ] Write failing tests for file selection, upload success, 400/413/422/500 messages, and disabled processing state.
- [ ] Implement drag/drop and selector UI with no client extraction or credentials.
- [ ] Verify tests and build.

### Task 6: Backend transport integration and verification

**Files:** Modify `app/main.py` only if CORS or static serving is required; update `README.md` with exact UI run instructions and URL.

- [ ] First run the frontend against the existing API and confirm whether CORS is required.
- [ ] If required, add narrowly scoped localhost CORS middleware without changing routes or schemas.
- [ ] Run frontend tests/build, `python -m pytest -q`, OpenAPI route/schema checks, and `git diff --check`.
- [ ] Audit the final diff for credentials, `.env` access, analytical-service changes, and unintended backend API changes.
