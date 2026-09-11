# PRISM Web UI Design

## Goal

Add a production-quality React/TypeScript interface over the existing FastAPI analytical APIs without duplicating analytical logic or changing backend semantics.

## Architecture

The frontend lives in `frontend/` and uses Vite, React, TypeScript, and Vitest. A single typed API client owns all HTTP access. Route-level pages compose reusable presentation components for project summaries, activity lists, activity detail, history, and upload states. The backend remains the only source of forecast, evidence-quality, risk, and decision-support results.

The FastAPI application receives only minimal transport integration if required: CORS for local Vite development and static serving only if a production run mode is practical without altering API behavior. No analytical service or schema semantics change.

## User-facing routes

- `/` redirects to the first project or shows the empty-project state.
- `/projects` lists available projects.
- `/projects/:projectName` shows the project dashboard and activity table.
- `/projects/:projectName/activities/:activityName` shows activity history and predictive detail.
- `/reports` provides upload and processing feedback.

## Data boundaries

The UI consumes `/api/v1/projects`, project predictive summary, activity predictive summary, activity history, optional trend/risk/insight/issue/schedule-impact endpoints, and `/api/v1/upload`. Client-side filtering only compares categorical fields already returned by the backend; it does not derive scores, dates, trends, confidence, risk, or aggregates.

## Quality and security

Loading, empty, 404, validation, network, insufficient-data, and unavailable states are explicit. No frontend credential or `.env` value is read. The upload UI reflects backend-supported extensions and limits discovered from configuration without reimplementing extraction.
