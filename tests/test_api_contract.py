import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import app.api.upload as upload_module

    app.state.analysis_service = AnalysisService()
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(upload_module, "process_file", lambda path: {
        "file_type": "pdf",
        "document_type": "digital_pdf",
        "processing_method": "test",
        "content": "processed",
        "extracted_data": {},
    })
    with TestClient(app) as test_client:
        yield test_client


def _error_body(response):
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    return body["error"]


def test_root_returns_typed_response(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "PRISM is running"}


def test_health_returns_typed_response(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "PRISM"}


def test_projects_returns_typed_response(client):
    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    assert response.json() == {"projects": []}


def test_upload_returns_typed_response_and_created_status(client, monkeypatch):
    import app.api.upload as upload_module

    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.pdf", b"report")},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "file_id",
        "original_filename",
        "stored_filename",
        "status",
        "processing_result",
    }
    assert body["original_filename"] == "report.pdf"
    assert body["status"] == "processed"


def test_missing_upload_file_has_consistent_error(client):
    response = client.post("/api/v1/upload")

    assert response.status_code == 400
    assert _error_body(response)["code"] == "missing_file"


def test_unsupported_extension_has_consistent_error(client):
    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.txt", b"report")},
    )

    assert response.status_code == 400
    error = _error_body(response)
    assert error["code"] == "unsupported_file_type"
    assert "report.txt" not in error["message"]


def test_empty_upload_has_consistent_error(client):
    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.pdf", b"")},
    )

    assert response.status_code == 400
    assert _error_body(response)["code"] == "empty_file"


def test_oversized_upload_has_consistent_error(client):
    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.pdf", b"x" * (10 * 1024 * 1024 + 1))},
    )

    assert response.status_code == 413
    assert _error_body(response)["code"] == "file_too_large"


def test_malformed_file_has_safe_client_error(client, monkeypatch):
    import app.api.upload as upload_module

    monkeypatch.setattr(
        upload_module,
        "process_file",
        lambda path: (_ for _ in ()).throw(ValueError("private parser path")),
    )
    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.pdf", b"report")},
    )

    assert response.status_code == 400
    error = _error_body(response)
    assert error["code"] == "invalid_file"
    assert "private parser path" not in json.dumps(response.json())


def test_extraction_failure_has_safe_server_error(client, monkeypatch):
    import app.api.upload as upload_module

    monkeypatch.setattr(
        upload_module,
        "process_file",
        lambda path: (_ for _ in ()).throw(RuntimeError("provider secret")),
    )
    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.pdf", b"report")},
    )

    assert response.status_code == 500
    error = _error_body(response)
    assert error["code"] == "processing_failed"
    assert "provider secret" not in json.dumps(response.json())


def test_failed_upload_file_is_cleaned_up(client, tmp_path, monkeypatch):
    import app.api.upload as upload_module

    monkeypatch.setattr(
        upload_module,
        "process_file",
        lambda path: (_ for _ in ()).throw(RuntimeError("failure")),
    )
    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.pdf", b"report")},
    )

    assert response.status_code == 500
    assert list(tmp_path.iterdir()) == []


def test_spreadsheet_upload_has_stable_processing_result_contract(
    client,
    monkeypatch,
):
    import app.api.upload as upload_module

    monkeypatch.setattr(
        upload_module,
        "process_file",
        lambda path: {
            "file_type": "csv",
            "document_type": "structured_data",
            "processing_method": "pandas",
            "content": [{"activity": "Foundation", "progress": 40}],
        },
    )
    response = client.post(
        "/api/v1/upload",
        files={"file": ("report.csv", b"activity,progress\nFoundation,40")},
    )

    assert response.status_code == 201
    assert response.json()["processing_result"]["content"] == [
        {"activity": "Foundation", "progress": 40}
    ]


def test_unknown_project_and_activity_use_consistent_error_shape(client):
    unknown_project = client.get("/api/v1/projects/Unknown/trends")
    app.state.analysis_service.record_report(
        ProgressReport(
            project_name="Known",
            activities=[ActivityProgress(activity_name="Known activity")],
        )
    )
    unknown_activity = client.get(
        "/api/v1/projects/Known/activities/Unknown/history"
    )

    assert unknown_project.status_code == 404
    assert unknown_activity.status_code == 404
    assert set(unknown_project.json()) == {"error"}
    assert set(unknown_activity.json()) == {"error"}
    assert _error_body(unknown_project)["code"] == "project_not_found"
    assert _error_body(unknown_activity)["code"] == "activity_not_found"


def test_public_endpoints_expose_response_models_in_openapi(client):
    schema = client.get("/openapi.json").json()

    assert schema["paths"]["/"]["get"]["responses"]["200"]["content"]
    assert schema["paths"]["/health"]["get"]["responses"]["200"]["content"]
    assert schema["paths"]["/api/v1/projects"]["get"]["responses"]["200"]["content"]
    assert schema["paths"]["/api/v1/upload"]["post"]["responses"]["201"]["content"]
