# PRISM

PRISM (Project Report Intelligence & Site Monitoring) is a FastAPI backend
that turns construction progress reports into validated structured data and
deterministic progress, risk, and explainable insight results.

## Current scope

The current backend supports:

- PDF, image, Excel, and CSV uploads
- PDF text extraction and OCR fallback
- Structured Gemini extraction for document text
- Pydantic validation and normalization
- In-memory report recording
- Activity history, trend analysis, observed-risk scoring, and explainable insights
- A versioned HTTP API under `/api/v1`

Data is currently held in memory for the running process. Persistence,
authentication, forecasting, and notifications are outside the current scope.

## Architecture

```text
Upload API
  -> file router
  -> extraction services
  -> Pydantic validation
  -> in-memory analysis service
  -> history, trends, risks, and insights APIs
```

The application boundary is in `app/api/`. Domain schemas are in
`app/schemas/`, while extraction and analysis components are in `app/services/`.

## Setup

Create and activate a virtual environment, then install the declared
dependencies:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a local `.env` file with the Gemini credential used for AI extraction:

```text
GEMINI_API_KEY=your_gemini_api_key
```

Never commit credentials. The existing tracked `.env` requires separate
credential remediation and is intentionally not changed by this step.

## Run the API

```powershell
uvicorn app.main:app --reload
```

Interactive API documentation is available at `/docs`; the OpenAPI document
is available at `/openapi.json`.

## Configuration

The following settings can be provided through environment variables or `.env`:

| Setting | Default | Purpose |
|---|---:|---|
| `GEMINI_API_KEY` | required | Gemini extraction credential |
| `UPLOAD_DIR` | `data/uploads` | Directory for uploaded files |
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` | Maximum upload size, 10 MiB |
| `ALLOWED_EXTENSIONS` | PDF/images/spreadsheets | Supported filename extensions |

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Service message |
| GET | `/health` | Health status |
| POST | `/api/v1/upload` | Process an uploaded report |
| GET | `/api/v1/projects` | List recorded projects |
| GET | `/api/v1/projects/{project_name}/activities/{activity_name}/history` | Activity history |
| GET | `/api/v1/projects/{project_name}/trends` | Project activity trends |
| GET | `/api/v1/projects/{project_name}/activities/{activity_name}/trend` | Activity trend |
| GET | `/api/v1/projects/{project_name}/risks` | Project activity risks |
| GET | `/api/v1/projects/{project_name}/activities/{activity_name}/risk` | Activity risk |
| GET | `/api/v1/projects/{project_name}/insights` | Project explainable insights |
| GET | `/api/v1/projects/{project_name}/activities/{activity_name}/insight` | Activity explainable insight |

## Representative responses

Health:

```json
{
  "status": "healthy",
  "service": "PRISM"
}
```

Projects:

```json
{
  "projects": ["Metro Project"]
}
```

Successful uploads return `201 Created`:

```json
{
  "file_id": "generated-uuid",
  "original_filename": "report.pdf",
  "stored_filename": "generated-uuid.pdf",
  "status": "processed",
  "processing_result": {
    "file_type": "pdf",
    "document_type": "digital_pdf",
    "processing_method": "direct_text_extraction"
  }
}
```

API errors use a small consistent structure:

```json
{
  "error": {
    "code": "unsupported_file_type",
    "message": "Uploaded file type is not supported"
  }
}
```

Unknown projects and activities return `404`. Invalid uploads return `400` or
`413`; extraction/processing failures return safe `500` responses without
filesystem paths, provider errors, or exception details.

## Run tests

```powershell
python -m pytest -v
```

The suite includes extraction, schema, recording, trend, risk, insight, API
contract, upload validation, error handling, cleanup, and OpenAPI coverage.

## Project status

Phase 1 document intelligence is complete. Phase 2 currently includes
deterministic history, trend, risk, explainable insight, and API-hardening work.
Predictive construction intelligence remains future work.
