from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService
from app.services.schedule_impact_analyzer import ScheduleImpactAnalyzer
from app.services.progress_tracker import ProgressTracker


def _report(
    *,
    project_name: str = "Metro Project",
    report_date: str | None = "1 June 2025",
    activity_name: str = "Foundation RCC work",
    progress: float | None = None,
    delay_hours: float | None = None,
    delay_reason: str | None = None,
) -> ProgressReport:
    return ProgressReport(
        project_name=project_name,
        report_date=report_date,
        activities=[
            ActivityProgress(
                activity_name=activity_name,
                progress_percentage=progress,
                delay_duration_hours=delay_hours,
                delay_reason=delay_reason,
            )
        ],
    )


def _analyze(*reports: ProgressReport):
    tracker = ProgressTracker()
    for report in reports:
        tracker.record(report)
    history = tracker.get_activity_history(
        reports[0].project_name,
        reports[0].activities[0].activity_name,
    )
    assert history is not None
    return ScheduleImpactAnalyzer(tracker).analyze_history(history)


def test_one_valid_delay_duration_is_available():
    result = _analyze(_report(delay_hours=8))

    assert result.status == "available"
    assert result.delay_observation_count == 1
    assert result.latest_delay_hours == 8
    assert result.latest_delay_reason is None
    assert "reported" in result.summary.lower()


def test_multiple_reported_durations_are_observations_not_slippage():
    result = _analyze(
        _report(report_date="1 June 2025", delay_hours=8),
        _report(report_date="8 June 2025", delay_hours=8),
        _report(report_date="15 June 2025", delay_hours=8),
    )

    assert result.delay_observation_count == 3
    assert result.latest_delay_hours == 8
    assert "24" not in result.summary
    assert all(
        phrase not in result.summary.lower()
        for phrase in ("behind schedule", "schedule slippage")
    )


def test_missing_duration_is_allowed_for_reason_only_observation():
    result = _analyze(_report(delay_reason="Heavy rainfall"))

    assert result.status == "available"
    assert result.delay_observation_count == 1
    assert result.latest_delay_hours is None
    assert result.latest_delay_reason == "Heavy rainfall"


def test_zero_duration_is_a_valid_observation():
    result = _analyze(_report(delay_hours=0))

    assert result.status == "available"
    assert result.delay_observation_count == 1
    assert result.latest_delay_hours == 0


def test_negative_duration_is_not_a_delay_observation():
    result = _analyze(_report(delay_hours=-2))

    assert result.status == "insufficient_data"
    assert result.delay_observation_count == 0
    assert result.latest_delay_hours is None


def test_repeated_delay_reasons_are_normalized_and_ordered_by_first_observation():
    result = _analyze(
        _report(
            report_date="1 June 2025",
            delay_reason=" Heavy rainfall ",
        ),
        _report(
            report_date="8 June 2025",
            delay_reason="Material shortage",
        ),
        _report(
            report_date="15 June 2025",
            delay_reason="heavy rainfall",
        ),
        _report(
            report_date="22 June 2025",
            delay_reason=" material shortage ",
        ),
    )

    assert result.repeated_delay_reasons == [
        "Heavy rainfall",
        "Material shortage",
    ]


def test_latest_delay_uses_chronological_order():
    result = _analyze(
        _report(report_date="15 June 2025", delay_hours=12),
        _report(report_date="1 June 2025", delay_reason="Rain"),
    )

    assert result.latest_delay_hours is not None
    assert result.latest_delay_hours == 12
    assert result.latest_delay_reason is None


def test_unparseable_date_uses_submission_order_for_latest_delay():
    result = _analyze(
        _report(report_date=None, delay_hours=4),
        _report(report_date="date unavailable", delay_reason="Rain"),
    )

    assert result.latest_delay_hours is None
    assert result.latest_delay_reason == "Rain"


def test_progress_trend_is_passthrough_from_trend_analyzer():
    result = _analyze(
        _report(report_date="1 June 2025", progress=35, delay_hours=8),
        _report(report_date="8 June 2025", progress=50),
    )

    assert result.progress_trend == "improving"


def test_progress_trend_can_be_insufficient_while_schedule_impact_is_available():
    result = _analyze(_report(progress=None, delay_reason="Rain"))

    assert result.status == "available"
    assert result.progress_trend == "insufficient_data"


def test_no_delay_observations_are_insufficient_data():
    result = _analyze(
        _report(report_date="1 June 2025"),
        _report(report_date="8 June 2025"),
    )

    assert result.status == "insufficient_data"
    assert result.delay_observation_count == 0
    assert result.repeated_delay_reasons == []
    assert result.summary == "No valid delay duration or delay reason was reported."


def test_activity_and_project_isolation():
    tracker = ProgressTracker()
    tracker.record(_report(project_name="Project A", delay_reason="Rain"))
    tracker.record(
        _report(
            project_name="Project B",
            activity_name="Brick masonry work",
            delay_hours=6,
        )
    )
    service = AnalysisService(tracker)

    activity = service.analyze_activity_schedule_impact(
        "Project A",
        "Foundation RCC work",
    )
    other_activity = service.analyze_activity_schedule_impact(
        "Project A",
        "Brick masonry work",
    )

    assert activity is not None
    assert activity.delay_observation_count == 1
    assert other_activity is None


def test_project_results_are_deterministically_ordered():
    tracker = ProgressTracker()
    tracker.record(
        _report(activity_name="Zinc work", delay_hours=2)
    )
    tracker.record(
        _report(activity_name="Brick masonry work", delay_reason="Rain")
    )

    result = AnalysisService(tracker).analyze_project_schedule_impact(
        "Metro Project"
    )

    assert result is not None
    assert [activity.activity_name for activity in result.activities] == [
        "Brick masonry work",
        "Zinc work",
    ]


def test_schedule_impact_endpoints_return_typed_results_and_404s():
    app.state.analysis_service = AnalysisService()
    app.state.analysis_service.record_report(
        _report(delay_reason="Rain")
    )

    with TestClient(app) as client:
        project_response = client.get(
            "/api/v1/projects/Metro%20Project/schedule-impact"
        )
        activity_response = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/schedule-impact"
        )
        unknown_project = client.get(
            "/api/v1/projects/Unknown%20Project/schedule-impact"
        )
        unknown_activity = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Unknown%20work/schedule-impact"
        )

    assert project_response.status_code == 200
    assert project_response.json()["project_name"] == "Metro Project"
    assert project_response.json()["activities"][0]["status"] == "available"
    assert activity_response.status_code == 200
    assert activity_response.json()["status"] == "available"
    assert unknown_project.status_code == 404
    assert unknown_project.json()["error"]["code"] == "project_not_found"
    assert unknown_activity.status_code == 404
    assert unknown_activity.json()["error"]["code"] == "activity_not_found"


def test_schedule_impact_response_models_are_exposed_in_openapi():
    app.state.analysis_service = AnalysisService()

    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    components = schema["components"]["schemas"]
    assert "ActivityScheduleImpact" in components
    assert "ProjectScheduleImpact" in components
    assert schema["paths"][
        "/api/v1/projects/{project_name}/schedule-impact"
    ]["get"]["responses"]["200"]["content"]
    assert schema["paths"][
        "/api/v1/projects/{project_name}/activities/{activity_name}/schedule-impact"
    ]["get"]["responses"]["200"]["content"]
