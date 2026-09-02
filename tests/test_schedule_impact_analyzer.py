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


def test_schedule_impact_history_projects_one_valid_duration_observation():
    tracker = ProgressTracker()
    tracker.record(_report(delay_hours=8))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.observations[0].report_date == "1 June 2025"
    assert result.observations[0].delay_hours == 8
    assert result.observations[0].delay_reason is None
    assert result.observations[0].submission_order == 1


def test_schedule_impact_history_includes_multiple_observations():
    tracker = ProgressTracker()
    tracker.record(_report(report_date="1 June 2025", delay_hours=8))
    tracker.record(_report(report_date="8 June 2025", delay_reason="Rain"))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [(item.delay_hours, item.delay_reason) for item in result.observations] == [
        (8, None),
        (None, "Rain"),
    ]


def test_schedule_impact_history_applies_exact_delay_qualification_rules():
    tracker = ProgressTracker()
    tracker.record(_report(delay_hours=0))
    tracker.record(_report(report_date="8 June 2025", delay_hours=-2))
    tracker.record(_report(report_date="15 June 2025", delay_reason=" Rain "))
    tracker.record(_report(report_date="22 June 2025", delay_hours=4))
    tracker.record(_report(report_date="29 June 2025"))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [(item.delay_hours, item.delay_reason) for item in result.observations] == [
        (0, None),
        (None, "Rain"),
        (4, None),
    ]


def test_boolean_delay_duration_is_not_valid_evidence():
    tracker = ProgressTracker()
    tracker.record(_report(delay_hours=True))
    tracker.record(_report(report_date="8 June 2025", delay_hours=False))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.observations == []


def test_invalid_duration_with_valid_reason_is_reason_only_evidence():
    tracker = ProgressTracker()
    tracker.record(
        _report(delay_hours=-2, delay_reason="Material shortage")
    )

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert len(result.observations) == 1
    assert result.observations[0].delay_hours is None
    assert result.observations[0].delay_reason == "Material shortage"


def test_whitespace_only_reason_does_not_qualify_by_itself():
    tracker = ProgressTracker()
    tracker.record(_report(delay_reason="   \t  "))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.observations == []


def test_schedule_impact_history_orders_by_date_then_submission_order():
    tracker = ProgressTracker()
    tracker.record(_report(report_date="15 June 2025", delay_hours=12))
    tracker.record(_report(report_date="1 June 2025", delay_hours=4))
    tracker.record(_report(report_date="1 June 2025", delay_reason="Rain"))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [item.submission_order for item in result.observations] == [2, 3, 1]
    assert [item.report_date for item in result.observations] == [
        "1 June 2025",
        "1 June 2025",
        "15 June 2025",
    ]


def test_schedule_impact_history_falls_back_to_submission_order_for_partial_dates():
    tracker = ProgressTracker()
    tracker.record(_report(report_date="15 June 2025", delay_hours=12))
    tracker.record(_report(report_date=None, delay_reason="Rain"))
    tracker.record(_report(report_date="1 June 2025", delay_hours=4))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [item.submission_order for item in result.observations] == [1, 2, 3]


def test_excluded_undated_snapshot_still_triggers_submission_order_fallback():
    tracker = ProgressTracker()
    tracker.record(_report(report_date=None))
    tracker.record(_report(report_date="15 June 2025", delay_hours=12))
    tracker.record(_report(report_date="1 June 2025", delay_hours=4))

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert [item.submission_order for item in result.observations] == [2, 3]


def test_schedule_impact_history_isolated_by_activity_and_project():
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

    result = service.analyze_activity_schedule_impact_history(
        "Project A",
        "Foundation RCC work",
    )

    assert result is not None
    assert len(result.observations) == 1
    assert service.analyze_activity_schedule_impact_history(
        "Project A",
        "Brick masonry work",
    ) is None
    assert service.analyze_activity_schedule_impact_history(
        "Project B",
        "Foundation RCC work",
    ) is None


def test_schedule_impact_history_returns_empty_observations_for_existing_activity():
    tracker = ProgressTracker()
    tracker.record(_report())

    result = AnalysisService(tracker).analyze_activity_schedule_impact_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.observations == []


def test_schedule_impact_history_service_returns_none_for_unknown_project():
    result = AnalysisService().analyze_activity_schedule_impact_history(
        "Unknown Project",
        "Foundation RCC work",
    )

    assert result is None


def test_schedule_impact_history_endpoint_returns_typed_result_and_404s():
    app.state.analysis_service = AnalysisService()
    app.state.analysis_service.record_report(_report(delay_reason="Rain"))

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/schedule-impact/history"
        )
        unknown_project = client.get(
            "/api/v1/projects/Unknown%20Project/activities/"
            "Foundation%20RCC%20work/schedule-impact/history"
        )
        unknown_activity = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Unknown%20work/schedule-impact/history"
        )

    assert response.status_code == 200
    assert response.json() == {
        "project_name": "Metro Project",
        "activity_name": "Foundation RCC work",
        "observations": [
            {
                "report_date": "1 June 2025",
                "delay_hours": None,
                "delay_reason": "Rain",
                "submission_order": 1,
            }
        ],
    }
    assert unknown_project.status_code == 404
    assert unknown_project.json()["error"]["code"] == "project_not_found"
    assert unknown_activity.status_code == 404
    assert unknown_activity.json()["error"]["code"] == "activity_not_found"


def test_schedule_impact_history_response_model_is_exposed_in_openapi():
    app.state.analysis_service = AnalysisService()

    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    components = schema["components"]["schemas"]
    assert "ScheduleImpactObservation" in components
    assert "ActivityScheduleImpactHistory" in components
    assert schema["paths"][
        "/api/v1/projects/{project_name}/activities/{activity_name}/schedule-impact/history"
    ]["get"]["responses"]["200"]["content"]


def test_project_schedule_impact_history_composes_all_activity_evidence():
    tracker = ProgressTracker()
    tracker.record(
        _report(
            activity_name="Zinc work",
            delay_hours=2,
        )
    )
    tracker.record(
        _report(
            activity_name="Brick masonry work",
            delay_reason="Rain",
        )
    )

    result = AnalysisService(tracker).analyze_project_schedule_impact_history(
        "Metro Project",
    )

    assert result is not None
    assert result.project_name == "Metro Project"
    assert [activity.activity_name for activity in result.activities] == [
        "Brick masonry work",
        "Zinc work",
    ]
    assert result.activities[0].observations[0].delay_reason == "Rain"
    assert result.activities[1].observations[0].delay_hours == 2


def test_project_schedule_impact_history_includes_activities_with_empty_evidence():
    tracker = ProgressTracker()
    tracker.record(
        _report(
            activity_name="Foundation RCC work",
            delay_hours=4,
        )
    )
    tracker.record(
        _report(
            activity_name="Site cleanup",
        )
    )

    result = AnalysisService(tracker).analyze_project_schedule_impact_history(
        "Metro Project",
    )

    assert result is not None
    cleanup = next(
        activity
        for activity in result.activities
        if activity.activity_name == "Site cleanup"
    )
    assert cleanup.observations == []


def test_project_schedule_impact_history_preserves_each_activity_ordering():
    tracker = ProgressTracker()
    tracker.record(
        _report(
            activity_name="Foundation RCC work",
            report_date="15 June 2025",
            delay_hours=12,
        )
    )
    tracker.record(
        _report(
            activity_name="Foundation RCC work",
            report_date="1 June 2025",
            delay_hours=4,
        )
    )
    tracker.record(
        _report(
            activity_name="Brick masonry work",
            report_date=None,
            delay_reason="Rain",
        )
    )
    tracker.record(
        _report(
            activity_name="Brick masonry work",
            report_date="1 June 2025",
            delay_hours=2,
        )
    )

    result = AnalysisService(tracker).analyze_project_schedule_impact_history(
        "Metro Project",
    )

    assert result is not None
    foundation = next(
        activity
        for activity in result.activities
        if activity.activity_name == "Foundation RCC work"
    )
    masonry = next(
        activity
        for activity in result.activities
        if activity.activity_name == "Brick masonry work"
    )
    assert [item.submission_order for item in foundation.observations] == [2, 1]
    assert [item.submission_order for item in masonry.observations] == [3, 4]


def test_project_schedule_impact_history_service_returns_none_for_unknown_project():
    result = AnalysisService().analyze_project_schedule_impact_history(
        "Unknown Project",
    )

    assert result is None


def test_project_schedule_impact_history_endpoint_returns_typed_result_and_404():
    app.state.analysis_service = AnalysisService()
    app.state.analysis_service.record_report(
        _report(activity_name="Foundation RCC work", delay_hours=4)
    )
    app.state.analysis_service.record_report(
        _report(activity_name="Site cleanup")
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/projects/Metro%20Project/schedule-impact/history"
        )
        unknown_project = client.get(
            "/api/v1/projects/Unknown%20Project/schedule-impact/history"
        )

    assert response.status_code == 200
    assert response.json()["project_name"] == "Metro Project"
    site_cleanup = next(
        activity
        for activity in response.json()["activities"]
        if activity["activity_name"] == "Site cleanup"
    )
    assert site_cleanup["observations"] == []
    assert unknown_project.status_code == 404
    assert unknown_project.json()["error"]["code"] == "project_not_found"


def test_project_schedule_impact_history_response_model_is_exposed_in_openapi():
    app.state.analysis_service = AnalysisService()

    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    components = schema["components"]["schemas"]
    assert "ProjectScheduleImpactHistory" in components
    assert schema["paths"][
        "/api/v1/projects/{project_name}/schedule-impact/history"
    ]["get"]["responses"]["200"]["content"]
