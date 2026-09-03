from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_ui_route_serves_dashboard():
    with TestClient(app) as test_client:
        response = test_client.get("/ui")

    assert response.status_code == 200
    assert "PRISM" in response.text
    assert "app.js" in response.text


def test_ui_static_assets_are_served():
    with TestClient(app) as test_client:
        css_response = test_client.get("/ui/styles.css")
        js_response = test_client.get("/ui/app.js")

    assert css_response.status_code == 200
    assert "--ink" in css_response.text
    assert js_response.status_code == 200
    assert "loadProjectData" in js_response.text


def test_expected_dashboard_assets_exist():
    static_dir = PROJECT_ROOT / "app" / "static"

    assert (static_dir / "index.html").is_file()
    assert (static_dir / "styles.css").is_file()
    assert (static_dir / "app.js").is_file()


def test_ui_references_approved_api_endpoints():
    script = (PROJECT_ROOT / "app" / "static" / "app.js").read_text()
    assert 'const API_BASE = "/api/v1"' in script
    endpoints = [
        "/projects",
        "/upload",
        "/trends",
        "/risks",
        "/insights",
        "/schedule-impact",
        "/schedule-impact/history",
        "/issues/history",
    ]

    for endpoint in endpoints:
        assert endpoint in script


def test_existing_root_and_health_routes_remain_available():
    with TestClient(app) as test_client:
        root_response = test_client.get("/")
        health_response = test_client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json() == {"message": "PRISM is running"}
    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "healthy",
        "service": "PRISM",
    }
