from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService
from app.services.progress_tracker import ProgressTracker


def _report(
    *,
    project_name: str = "Metro Project",
    report_date: str | None = "1 June 2025",
    activity_name: str = "Foundation RCC work",
    issues: list[str] | None = None,
) -> ProgressReport:
    return ProgressReport(
        project_name=project_name,
        report_date=report_date,
        activities=[
            ActivityProgress(
                activity_name=activity_name,
                issues=issues or [],
            )
        ],
    )


def test_activity_issue_history_projects_trimmed_issue_with_source_metadata():
    tracker = ProgressTracker()
    tracker.record(_report(issues=["  Material shortage  "]))

    result = AnalysisService(tracker).analyze_activity_issue_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [observation.model_dump() for observation in result.observations] == [
        {
            "report_date": "1 June 2025",
            "issue": "Material shortage",
            "submission_order": 1,
        }
    ]


def test_activity_issue_history_preserves_multiple_and_duplicate_issue_entries():
    tracker = ProgressTracker()
    tracker.record(
        _report(issues=["Material shortage", "Access blocked", "Material shortage"])
    )

    result = AnalysisService(tracker).analyze_activity_issue_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [observation.issue for observation in result.observations] == [
        "Material shortage",
        "Access blocked",
        "Material shortage",
    ]


def test_blank_issue_entries_are_excluded():
    tracker = ProgressTracker()
    tracker.record(_report(issues=["   ", "\t"]))

    result = AnalysisService(tracker).analyze_activity_issue_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.observations == []


def test_activity_issue_history_orders_parseable_dates_then_submission_order():
    tracker = ProgressTracker()
    tracker.record(
        _report(report_date="15 June 2025", issues=["Later"])
    )
    tracker.record(
        _report(report_date="1 June 2025", issues=["Earlier"])
    )
    tracker.record(
        _report(report_date="1 June 2025", issues=["Tie"])
    )

    result = AnalysisService(tracker).analyze_activity_issue_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [observation.submission_order for observation in result.observations] == [
        2,
        3,
        1,
    ]


def test_excluded_undated_snapshot_still_triggers_submission_order_fallback():
    tracker = ProgressTracker()
    tracker.record(_report(report_date=None))
    tracker.record(_report(report_date="15 June 2025", issues=["Later"]))
    tracker.record(_report(report_date="1 June 2025", issues=["Earlier"]))

    result = AnalysisService(tracker).analyze_activity_issue_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [observation.submission_order for observation in result.observations] == [
        2,
        3,
    ]


def test_project_issue_history_preserves_activity_order_and_empty_evidence():
    tracker = ProgressTracker()
    tracker.record(
        _report(activity_name="Zinc work", issues=["Cracking"])
    )
    tracker.record(_report(activity_name="Site cleanup"))

    result = AnalysisService(tracker).analyze_project_issue_history(
        "Metro Project",
    )

    assert result is not None
    assert [activity.activity_name for activity in result.activities] == [
        "Site cleanup",
        "Zinc work",
    ]
    assert result.activities[0].observations == []
    assert result.activities[1].observations[0].issue == "Cracking"


def test_issue_evidence_isolated_by_activity_and_project():
    tracker = ProgressTracker()
    tracker.record(_report(project_name="Project A", issues=["Rain"]))
    tracker.record(
        _report(
            project_name="Project B",
            activity_name="Brick masonry work",
            issues=["Access blocked"],
        )
    )
    service = AnalysisService(tracker)

    result = service.analyze_activity_issue_history(
        "Project A",
        "Foundation RCC work",
    )

    assert result is not None
    assert [observation.issue for observation in result.observations] == [
        "Rain"
    ]
    assert service.analyze_activity_issue_history(
        "Project A",
        "Brick masonry work",
    ) is None
    assert service.analyze_activity_issue_history(
        "Project B",
        "Foundation RCC work",
    ) is None


def test_issue_evidence_service_returns_none_for_unknown_resources():
    service = AnalysisService()

    assert service.analyze_project_issue_history("Unknown Project") is None
    assert service.analyze_activity_issue_history(
        "Unknown Project",
        "Foundation RCC work",
    ) is None


def test_issue_evidence_endpoints_return_typed_results_and_existing_errors():
    app.state.analysis_service = AnalysisService()
    app.state.analysis_service.record_report(
        _report(issues=["  Material shortage  "])
    )

    with TestClient(app) as client:
        activity_response = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/issues/history"
        )
        project_response = client.get(
            "/api/v1/projects/Metro%20Project/issues/history"
        )
        unknown_project = client.get(
            "/api/v1/projects/Unknown%20Project/issues/history"
        )
        unknown_activity = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Unknown%20work/issues/history"
        )

    assert activity_response.status_code == 200
    assert activity_response.json()["observations"][0]["issue"] == (
        "Material shortage"
    )
    assert project_response.status_code == 200
    assert project_response.json()["activities"][0]["observations"]
    assert unknown_project.status_code == 404
    assert unknown_project.json()["error"]["code"] == "project_not_found"
    assert unknown_activity.status_code == 404
    assert unknown_activity.json()["error"]["code"] == "activity_not_found"


def test_issue_evidence_response_models_and_routes_are_in_openapi():
    app.state.analysis_service = AnalysisService()

    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    components = schema["components"]["schemas"]
    assert "IssueObservation" in components
    assert "ActivityIssueHistory" in components
    assert "ProjectIssueHistory" in components
    assert schema["paths"][
        "/api/v1/projects/{project_name}/activities/{activity_name}/issues/history"
    ]["get"]["responses"]["200"]["content"]
    assert schema["paths"][
        "/api/v1/projects/{project_name}/issues/history"
    ]["get"]["responses"]["200"]["content"]
