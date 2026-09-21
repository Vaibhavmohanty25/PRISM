# PRISM

## Project Report Intelligence & Site Monitoring

PRISM is an AI-powered construction document intelligence and project monitoring platform designed to turn messy construction progress reports into structured, explainable, and actionable project insights.

Construction teams often work with progress information scattered across PDFs, scanned documents, spreadsheets, images, and manually prepared reports. PRISM provides a pipeline for extracting this information, tracking activity progress over time, identifying observed risks, forecasting activity completion, evaluating forecast evidence quality, detecting predictive risk, and presenting the results through REST APIs and a web dashboard.

The system combines **AI-assisted document extraction** with **deterministic analytical layers**, keeping predictive outputs explainable and traceable back to observed project evidence.

---

# What PRISM Does

PRISM follows a pipeline like this:

```text
Construction Report
        |
        v
Document Processing
        |
        v
AI-Assisted Information Extraction
        |
        v
Structured Project Data
        |
        v
Historical Progress Tracking
        |
        +----------------------+
        |                      |
        v                      v
Observed Analytics      Forecasting Engine
        |                      |
        v                      v
Risk / Trends          Evidence Quality
        |                      |
        +----------+-----------+
                   |
                   v
            Predictive Risk
                   |
                   v
            Decision Support
                   |
                   v
        Project Predictive Summary
                   |
                   v
            REST API + Web UI
```

The main goal is not just to extract information from construction reports, but to convert historical project evidence into useful and explainable monitoring intelligence.

---

# Key Features

## 1. Construction Document Intelligence

PRISM processes construction progress reports and converts unstructured information into structured project data.

The extraction pipeline supports document-oriented workflows such as:

- PDF construction reports
- Scanned reports
- Images
- Excel/CSV-based project information
- Activity progress
- Delays
- Issues
- Project metadata
- Report dates

The backend uses AI-assisted extraction while keeping downstream analytical logic deterministic.

---

## 2. Historical Progress Tracking

PRISM maintains historical observations for individual construction activities.

Each accepted report contributes an activity snapshot containing information such as:

```text
Activity
Progress %
Report Date
Delay Information
Issues
Submission Order
```

This allows PRISM to reconstruct how an activity has evolved across multiple reports instead of treating every document independently.

Duplicate observations are handled conservatively to prevent the same report from incorrectly influencing project analytics.

---

## 3. Trend Analysis

Historical activity observations are used to determine progress trends.

PRISM analyzes:

- first observed progress
- latest observed progress
- progress delta
- historical movement
- progress velocity
- observation count

The trend layer uses deterministic rules rather than an LLM-generated interpretation.

---

## 4. Observed Risk Analysis

PRISM separates **observed risk** from **predictive risk**.

Observed risk is based on evidence already present in project history, including things such as:

- reported delays
- recurring issues
- historical progress behavior
- observed project conditions

This prevents future-facing predictions from being confused with issues that have already been directly observed.

---

# Predictive Construction Intelligence

PRISM adds a deterministic predictive layer on top of the historical project data.

The predictive system is intentionally designed to avoid black-box predictions.

Instead, each output can be explained using the historical observations that produced it.

---

## 5. Activity Completion Forecasting

PRISM can estimate activity completion based on historical progress velocity.

The basic forecasting model is:

```text
remaining_progress = 100 - current_progress
```

Historical velocity:

```text
historical_velocity_per_day =
    (latest_progress - first_progress)
    / calendar_days_between_first_and_latest
```

Estimated remaining duration:

```text
estimated_days_to_completion =
    remaining_progress
    / historical_velocity_per_day
```

Estimated completion:

```text
estimated_completion_date =
    latest_usable_report_date
    + estimated_days_to_completion
```

The forecast method is:

```text
net_observed_progress_velocity
```

Forecast states include:

```text
available
insufficient_data
unavailable
```

PRISM does not fabricate a completion date when historical evidence cannot support one.

For example, zero or negative progress velocity will not be converted into an artificially positive forecast.

---

## 6. Forecast Evidence Quality

A completion estimate by itself is not enough.

PRISM therefore evaluates the **quality of the evidence supporting the forecast**.

Confidence is categorical:

```text
low
medium
high
```

This is deliberately **not a statistical probability**.

The system evaluates factors including:

- number of usable observations
- missing progress observations
- report-date quality
- same-day observations
- valid velocity intervals
- positive/zero/negative progress intervals
- direction consistency
- velocity stability

Confidence assessment states include:

```text
assessed
not_assessed
not_applicable
```

Velocity stability is represented as:

```text
stable
variable
unstable
not_assessable
```

Direction consistency is represented as:

```text
positive
mixed
non_positive
not_assessable
```

This gives users context about how much historical evidence exists behind a forecast.

---

## 7. Predictive Risk Analysis

PRISM evaluates future-facing activity risk separately from observed risk.

Predictive risk levels are:

```text
low
medium
high
not_assessed
not_applicable
```

Predictive risk is derived from historical trajectory characteristics such as:

- positive progress
- mixed progress
- non-positive progress
- stable velocity
- variable velocity
- unstable velocity

For example:

```text
Positive + Stable
        |
        v
       LOW

Mixed + Variable
        |
        v
      MEDIUM

Mixed + Unstable
        |
        v
       HIGH

Non-Positive Progress
        |
        v
       HIGH
```

Evidence quality and predictive risk remain separate concepts.

A lower-confidence forecast does **not automatically mean high risk**, and confidence is not used as a hidden risk score.

---

## 8. Decision Support

PRISM combines existing analytical outputs into an explainable activity-level decision-support layer.

Possible decision-support states include:

```text
supported
review_only
insufficient_evidence
not_applicable
```

Priority levels:

```text
none
low
medium
high
```

Recommended response categories:

```text
none
monitor
review
investigate
verify_data
```

Decision support considers structured outputs such as:

- observed risk
- predictive risk
- schedule-impact evidence
- recurring issue evidence
- forecast availability

The system does not autonomously modify schedules, allocate resources, approve spending, or perform project-management actions.

Its purpose is to surface evidence requiring human attention.

---

# Project Predictive Summary

PRISM also provides a project-level predictive overview.

The summary aggregates activity-level analytical results without inventing a new project-level prediction.

It includes information such as:

```text
Total Activities
Active Activities
Completed Activities

Forecast Status Distribution
Confidence Distribution
Predictive Risk Distribution
Decision Support Distribution
Priority Distribution
```

It also identifies:

```text
Activities Requiring Attention
Activities With Insufficient Evidence
Evidence Limitations
```

Completed activities remain represented in project statistics but are excluded from active attention queues.

---

# Explainability

Explainability is a core design principle of PRISM.

Instead of returning only:

```json
{
  "risk": "high"
}
```

PRISM keeps evidence explaining why an analytical result was produced.

Conceptually:

```json
{
  "level": "high",
  "evidence": [
    "Historical progress contains non-positive movement.",
    "Repeated activity issues were observed.",
    "Current trajectory requires review."
  ]
}
```

This makes the output easier to inspect, debug, and present to project stakeholders.

---

# Web Dashboard

PRISM includes a web interface built on top of the FastAPI backend.

The frontend provides views for:

- project monitoring
- predictive project summaries
- activity-level analysis
- completion forecasts
- forecast evidence quality
- predictive risk
- decision-support results
- historical evidence
- issue information
- schedule-impact information
- report upload workflows

The frontend acts as a presentation layer.

**Analytical logic remains in the backend.**

This prevents frontend and backend calculations from drifting apart.

---

# Technology Stack

## Backend

```text
Python
FastAPI
Pydantic
Uvicorn
REST APIs
```

## Document Intelligence

```text
Gemini API
OCR / document preprocessing
Structured extraction
PDF processing
```

## Analytics

```text
Python
Deterministic forecasting
Historical progress analysis
Trend analysis
Observed risk analysis
Forecast evidence-quality analysis
Predictive risk analysis
Decision-support rules
```

## Frontend

```text
React
TypeScript
Vite
CSS
REST API integration
```

## Testing

```text
pytest
FastAPI TestClient
Frontend tests
API contract testing
OpenAPI validation
```

---

# Project Architecture

A simplified repository structure looks like:

```text
PRISM/
|
├── app/
│   ├── api/
│   │   └── analysis.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── schemas/
│   │   └── project_data.py
│   │
│   ├── services/
│   │   ├── extraction_service.py
│   │   ├── progress_tracker.py
│   │   ├── trend_analyzer.py
│   │   ├── risk_analyzer.py
│   │   ├── forecast_analyzer.py
│   │   ├── forecast_confidence_analyzer.py
│   │   ├── predictive_risk_analyzer.py
│   │   ├── decision_support_analyzer.py
│   │   └── analysis_service.py
│   │
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.*
│
├── tests/
│   ├── test_forecast_analyzer.py
│   ├── test_forecast_confidence_analyzer.py
│   ├── test_predictive_risk_analyzer.py
│   ├── test_analysis_integration.py
│   ├── test_api_contract.py
│   └── test_project_predictive_summary.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The exact frontend file layout may vary as the UI evolves.

---

# API Overview

PRISM exposes its functionality through REST APIs.

## Health Check

```http
GET /health
```

---

## List Projects

```http
GET /api/v1/projects
```

---

## Activity Forecast

```http
GET /api/v1/projects/{project_name}/activities/{activity_name}/forecast
```

Returns the deterministic completion forecast together with forecast evidence quality and predictive risk information.

---

## Activity Decision Support

```http
GET /api/v1/projects/{project_name}/activities/{activity_name}/decision-support
```

Returns the activity-level decision-support result.

---

## Unified Activity Predictive Summary

```http
GET /api/v1/projects/{project_name}/activities/{activity_name}/predictive-summary
```

Provides a convenient frontend-facing response containing:

```text
Forecast
    ├── Evidence Quality
    └── Predictive Risk

Decision Support
```

---

## Project Predictive Summary

```http
GET /api/v1/projects/{project_name}/predictive-summary
```

Returns the project-level aggregation of activity predictive states.

---

## Document Upload

PRISM provides an upload workflow for processing construction reports through the extraction and analysis pipeline.

The exact request contract can be inspected through the automatically generated FastAPI documentation.

---

# Running PRISM Locally

## Prerequisites

Make sure you have:

```text
Python 3.x
Node.js
npm
Git
```

A Python virtual environment is strongly recommended.

---

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd PRISM
```

---

## 2. Create a Python Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If the project already contains your local virtual environment, simply activate it.

---

## 3. Install Backend Dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a local:

```text
.env
```

from:

```text
.env.example
```

Add the required credentials locally.

For example:

```env
GEMINI_API_KEY=your_api_key_here
```

Never commit the real `.env` file or API credentials to Git.

---

# Running the Backend

From the project root:

```powershell
uvicorn app.main:app --reload
```

The backend should start at:

```text
http://127.0.0.1:8000
```

Useful development routes:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

FastAPI Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# Running the Frontend

Open another terminal.

From the project root:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Vite will normally display a local address similar to:

```text
http://localhost:5173
```

Open the URL shown in the terminal.

---

# Quick Start

Use two terminals.

## Terminal 1 — Backend

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Terminal 2 — Frontend

```powershell
cd frontend
npm install
npm run dev
```

Then open:

```text
Frontend
http://localhost:5173

Backend API
http://127.0.0.1:8000

Swagger
http://127.0.0.1:8000/docs
```

---

# Running Tests

Activate the Python environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the backend test suite:

```powershell
pytest -q
```

For more detailed output:

```powershell
pytest -v
```

Frontend tests can be run from the frontend directory using the test command defined in `package.json`.

For example:

```powershell
cd frontend
npm test
```

or, depending on the configured script:

```powershell
npm run test
```

---

# Example Predictive Workflow

Suppose PRISM receives several reports for an activity:

```text
Activity: Foundation Work

Report 1
Progress: 20%
Date: 2026-08-01

Report 2
Progress: 35%
Date: 2026-08-06

Report 3
Progress: 50%
Date: 2026-08-11

Report 4
Progress: 65%
Date: 2026-08-16

Report 5
Progress: 80%
Date: 2026-08-21
```

PRISM can use these observations to determine:

```text
Historical Progress
        |
        v
Progress Velocity
        |
        v
Remaining Progress
        |
        v
Completion Forecast
        |
        v
Forecast Evidence Quality
        |
        v
Predictive Risk
        |
        v
Decision Support
```

The result is not simply:

```text
"Project looks fine."
```

Instead, PRISM provides structured outputs describing the forecast, strength of the historical evidence, trajectory risk, and the appropriate level of human attention.

---

# Design Principles

PRISM follows several important principles.

### Deterministic analytics

Forecasting, confidence assessment, predictive risk, and decision support use explicit rules rather than hidden LLM reasoning.

### Evidence before prediction

If there is not enough historical evidence, PRISM reports that limitation instead of fabricating a prediction.

### Observed and predictive risk remain separate

An existing problem and a possible future problem are not treated as the same thing.

### Confidence is not probability

Forecast evidence quality represents the strength and consistency of historical observations. It is not a percentage chance that the prediction will occur.

### Backend is the source of truth

The frontend displays analytical outputs returned by the backend instead of recreating analytical rules in JavaScript.

### Human decision-making remains central

PRISM provides decision support, not autonomous project management.

---

# What PRISM Does Not Claim

PRISM intentionally does not infer information that the available construction evidence cannot support.

The current system does not attempt to provide:

```text
Critical-path calculations
Dependency inference
Contractual completion predictions
Resource allocation optimization
Procurement decisions
Budget authorization
Recovery scheduling
Autonomous project-management actions
Statistical probability of completion
Black-box ML risk scores
```

These would require additional authoritative project information such as baseline schedules, dependencies, resource plans, contractual milestones, or cost data.

---

# Security

API credentials and environment-specific secrets must remain outside version control.

The repository uses `.gitignore` to prevent local environment files such as:

```text
.env
```

from being committed.

Developers should use:

```text
.env.example
```

to document required configuration without exposing real credentials.

If a credential is accidentally exposed, it should be rotated immediately and removed from reachable Git history rather than simply deleting it from the latest commit.

---

# Current Capabilities

PRISM currently provides an end-to-end foundation covering:

```text
Document Intelligence
        ↓
Structured Extraction
        ↓
Historical Progress Tracking
        ↓
Trend Analysis
        ↓
Observed Risk Analysis
        ↓
Schedule-Impact Evidence
        ↓
Issue Evidence History
        ↓
Deterministic Forecasting
        ↓
Forecast Evidence Quality
        ↓
Predictive Risk
        ↓
Decision Support
        ↓
Project Predictive Summary
        ↓
REST API
        ↓
Web Dashboard
```

---

# Why PRISM?

Construction progress information is often available, but fragmented.

A project manager may have dozens of reports containing useful signals, while extracting and comparing those signals manually becomes increasingly difficult as the project grows.

PRISM attempts to bridge that gap.

Instead of treating reports as static documents, it converts them into a growing historical evidence base that can be queried and analyzed.

That allows the system to answer questions such as:

```text
How has this activity progressed over time?

Is progress moving consistently?

What problems have repeatedly appeared?

Is there enough evidence to estimate completion?

How reliable is the historical evidence behind that estimate?

Does the current trajectory indicate predictive risk?

Which activities currently require human attention?
```

That transformation—from **documents to historical evidence to explainable intelligence**—is the core idea behind PRISM.

---

# Future Scope

Possible future extensions include:

- integration with authoritative baseline schedules
- planned-vs-actual progress comparison
- dependency-aware schedule analysis
- critical-path integration
- richer construction reporting dashboards
- role-based project access
- persistent project storage
- cloud deployment
- multi-project portfolio monitoring
- configurable analytical policies
- exportable project intelligence reports
- integration with construction-management platforms

These capabilities should be added only when the required authoritative project data is available.

---

# Project Status

PRISM has completed its core three-stage development roadmap:

```text
Document Intelligence
        +
Historical Construction Analytics
        +
Predictive Construction Intelligence
```

The current system includes deterministic forecasting, evidence-quality assessment, predictive risk, decision support, project-level predictive aggregation, REST API integration, automated testing, and a web interface.

The focus going forward is productization, deployment, richer project workflows, and integration with real-world construction data sources rather than changing the established analytical semantics.

---

# Author

**Vaibhav Mohanty**

B.Tech Computer Science & Engineering  
Artificial Intelligence & Machine Learning

---

# Disclaimer

PRISM is a decision-support and project intelligence system.

Forecasts, predictive risk levels, and decision-support outputs are derived from the project evidence available to the system. They should not be interpreted as contractual guarantees, engineering certifications, safety determinations, or replacements for professional construction-management judgment.
