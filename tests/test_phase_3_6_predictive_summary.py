from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService


def _record_reports(service: AnalysisService) -> None:
    service.record_report(
        ProgressReport(
            project_name="  Metro Project  ",
            report_date="1 June 2025",
            activities=[
                ActivityProgress(
                    activity_name=" Foundation RCC work ",
                    progress_percentage=35,
                )
            ],
        )
    )
    service.record_report(
        ProgressReport(
            project_name="metro project",
            report_date="15 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Foundation RCC work",
                    progress_percentage=57,
                )
            ],
        )
    )


def _client_with_reports() -> TestClient:
    app.state.analysis_service = AnalysisService()
    _record_reports(app.state.analysis_service)
    return TestClient(app)


def test_unified_activity_predictive_summary_preserves_existing_outputs():
    with _client_with_reports() as client:
        response = client.get(
            "/api/v1/projects/%20METRO%20PROJECT%20/activities/"
            "foundation%20rcc%20work/predictive-summary"
        )
        forecast = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/forecast"
        )
        decision_support = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/decision-support"
        )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "project_name",
        "activity_name",
        "forecast",
        "decision_support",
    }
    assert body["project_name"] == "Metro Project"
    assert body["activity_name"] == "Foundation RCC work"
    assert body["forecast"] == forecast.json()
    assert body["decision_support"] == decision_support.json()
    assert body["forecast"]["confidence"] is not None
    assert body["forecast"]["predictive_risk"] is not None


def test_unified_activity_predictive_summary_returns_consistent_not_found_errors():
    with _client_with_reports() as client:
        unknown_project = client.get(
            "/api/v1/projects/Unknown%20Project/activities/Task/"
            "predictive-summary"
        )
        unknown_activity = client.get(
            "/api/v1/projects/Metro%20Project/activities/Unknown/"
            "predictive-summary"
        )

    assert unknown_project.status_code == 404
    assert unknown_project.json()["error"]["code"] == "project_not_found"
    assert unknown_activity.status_code == 404
    assert unknown_activity.json()["error"]["code"] == "activity_not_found"


def test_unified_activity_predictive_summary_computes_forecast_once(monkeypatch):
    service = AnalysisService()
    _record_reports(service)
    calls = 0
    original = service.analyze_activity_forecast

    def counted_forecast(project_name, activity_name):
        nonlocal calls
        calls += 1
        return original(project_name, activity_name)

    monkeypatch.setattr(service, "analyze_activity_forecast", counted_forecast)
    app.state.analysis_service = service

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/predictive-summary"
        )

    assert response.status_code == 200
    assert calls == 1


def test_unified_activity_predictive_summary_openapi_contract():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    path = (
        "/api/v1/projects/{project_name}/activities/"
        "{activity_name}/predictive-summary"
    )
    response_schema = schema["paths"][path]["get"]["responses"]["200"]
    assert response_schema["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ActivityPredictiveSummary"
    )

    components = schema["components"]["schemas"]
    activity_summary = components["ActivityPredictiveSummary"]
    assert set(activity_summary["properties"]) == {
        "project_name",
        "activity_name",
        "forecast",
        "decision_support",
    }
    assert activity_summary["properties"]["forecast"]["$ref"].endswith(
        "/ForecastResult"
    )
    assert activity_summary["properties"]["decision_support"]["$ref"].endswith(
        "/DecisionSupport"
    )
    prohibited = {
        "probability",
        "predictive_risk_score",
        "project_completion_prediction",
        "target_date",
        "critical_path",
        "dependency",
        "resource_recommendation",
        "autonomous_action",
    }
    assert not prohibited.intersection(activity_summary["properties"])
