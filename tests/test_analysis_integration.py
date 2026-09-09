from fastapi.testclient import TestClient
import importlib

from app.main import app
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService


def _report(
    *,
    project_name: str = "Metro Project",
    report_date: str = "1 June 2025",
    progress: float = 35,
    activity_name: str = "Foundation RCC work",
) -> ProgressReport:
    return ProgressReport(
        project_name=project_name,
        report_date=report_date,
        activities=[
            ActivityProgress(
                activity_name=activity_name,
                progress_percentage=progress,
            )
        ],
    )


def test_recording_same_report_twice_keeps_one_snapshot():
    service = AnalysisService()
    report = _report()

    service.record_report(report)
    service.record_report(report)

    history = service.get_activity_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert history is not None
    assert len(history.snapshots) == 1


def test_project_analysis_results_are_deterministically_ordered():
    service = AnalysisService()
    service.record_report(
        _report(activity_name="Zinc work")
    )
    service.record_report(
        _report(activity_name="Brick masonry work")
    )

    assert [
        result.activity_name
        for result in service.analyze_project_trends("Metro Project")
    ] == ["Brick masonry work", "Zinc work"]
    assert [
        result.activity_name
        for result in service.analyze_project_risks("Metro Project")
    ] == ["Brick masonry work", "Zinc work"]


def test_insufficient_history_returns_typed_analysis_results():
    service = AnalysisService()
    service.record_report(_report())

    trend = service.analyze_activity_trend(
        "Metro Project",
        "Foundation RCC work",
    )
    risk = service.analyze_activity_risk(
        "Metro Project",
        "Foundation RCC work",
    )

    assert trend is not None
    assert trend.trend == "insufficient_data"
    assert risk is not None
    assert risk.risk_level == "insufficient_data"


def test_forecast_composition_adds_predictive_risk_without_changing_existing_results():
    service = AnalysisService()
    first = _report(
        report_date="1 June 2025",
        progress=35,
        project_name="  Metro Project  ",
        activity_name=" Foundation RCC work ",
    )
    second = ProgressReport(
        project_name="metro project",
        report_date="15 June 2025",
        activities=[
            ActivityProgress(
                activity_name="Foundation RCC work",
                progress_percentage=57,
                issues=["Access problem"],
                delay_reason="Rain",
            )
        ],
    )
    service.record_report(first)
    service.record_report(second)

    direct = service.forecast_analyzer.analyze_activity(
        " METRO PROJECT ",
        "foundation rcc work",
    )
    composed = service.analyze_activity_forecast(
        " METRO PROJECT ",
        "foundation rcc work",
    )
    observed_risk = service.analyze_activity_risk(
        " METRO PROJECT ",
        "foundation rcc work",
    )

    assert direct is not None
    assert composed is not None
    assert observed_risk is not None
    assert composed.predictive_risk is not None
    assert composed.predictive_risk.level == "not_assessed"
    assert not hasattr(composed, "decision_support")
    decision_support = service.analyze_activity_decision_support(
        " METRO PROJECT ",
        "foundation rcc work",
    )
    assert decision_support is not None
    assert decision_support.status == "review_only"
    assert decision_support.trigger == "schedule_impact"
    assert composed.confidence is not None
    assert {
        field: getattr(composed, field)
        for field in (
            "status",
            "current_progress",
            "remaining_progress",
            "historical_velocity_per_day",
            "estimated_days_to_completion",
            "estimated_completion_date",
            "observation_count",
            "first_report_date",
            "latest_report_date",
            "forecast_method",
            "evidence",
            "data_note",
        )
    } == {
        field: getattr(direct, field)
        for field in (
            "status",
            "current_progress",
            "remaining_progress",
            "historical_velocity_per_day",
            "estimated_days_to_completion",
            "estimated_completion_date",
            "observation_count",
            "first_report_date",
            "latest_report_date",
            "forecast_method",
            "evidence",
            "data_note",
        )
    }
    assert observed_risk.risk_level == "low"


def test_duplicate_reports_do_not_change_predictive_risk():
    service = AnalysisService()
    report_one = _report(report_date="1 June 2025", progress=35)
    report_two = _report(report_date="15 June 2025", progress=57)

    service.record_report(report_one)
    service.record_report(report_two)
    first = service.analyze_activity_forecast(
        "Metro Project",
        "Foundation RCC work",
    )
    service.record_report(report_two)
    second = service.analyze_activity_forecast(
        " metro project ",
        "foundation rcc work",
    )

    assert first is not None
    assert second is not None
    assert first.predictive_risk == second.predictive_risk


def test_issue_and_delay_fields_do_not_change_predictive_risk():
    baseline = AnalysisService()
    with_evidence = AnalysisService()
    reports = (
        _report(report_date="1 June 2025", progress=35),
        _report(report_date="15 June 2025", progress=57),
    )
    evidence_reports = (
        ProgressReport(
            project_name="Metro Project",
            report_date="1 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Foundation RCC work",
                    progress_percentage=35,
                    issues=["Access problem"],
                    delay_reason="Rain",
                )
            ],
        ),
        ProgressReport(
            project_name="Metro Project",
            report_date="15 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Foundation RCC work",
                    progress_percentage=57,
                    issues=["Material shortage"],
                    delay_reason="Equipment failure",
                )
            ],
        ),
    )
    for report in reports:
        baseline.record_report(report)
    for report in evidence_reports:
        with_evidence.record_report(report)

    baseline_result = baseline.analyze_activity_forecast(
        "Metro Project",
        "Foundation RCC work",
    )
    evidence_result = with_evidence.analyze_activity_forecast(
        "Metro Project",
        "Foundation RCC work",
    )

    assert baseline_result is not None
    assert evidence_result is not None
    assert evidence_result.predictive_risk == baseline_result.predictive_risk


def test_analysis_endpoints_return_results_and_404_for_unknown_resources():
    app.state.analysis_service = AnalysisService()
    service = app.state.analysis_service
    service.record_report(_report())

    with TestClient(app) as client:
        projects = client.get("/api/v1/projects")
        history = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/history"
        )
        trends = client.get("/api/v1/projects/Metro%20Project/trends")
        risks = client.get("/api/v1/projects/Metro%20Project/risks")
        unknown_project = client.get(
            "/api/v1/projects/Unknown%20Project/trends"
        )
        unknown_activity = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Unknown%20work/history"
        )

    assert projects.status_code == 200
    assert projects.json() == {"projects": ["Metro Project"]}
    assert history.status_code == 200
    assert len(history.json()["snapshots"]) == 1
    assert trends.status_code == 200
    assert trends.json()[0]["trend"] == "insufficient_data"
    assert risks.status_code == 200
    assert risks.json()[0]["risk_level"] == "insufficient_data"
    assert unknown_project.status_code == 404
    assert unknown_activity.status_code == 404


def test_project_api_lookup_accepts_canonical_identity_aliases():
    app.state.analysis_service = AnalysisService()
    app.state.analysis_service.record_report(
        ProgressReport(
            project_name="  Metro Project  ",
            report_date="1 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Foundation RCC work",
                    progress_percentage=35,
                    issues=["Rain"],
                    delay_reason="Rain",
                )
            ],
        )
    )

    with TestClient(app) as client:
        projects = client.get("/api/v1/projects")
        trends = client.get("/api/v1/projects/%20metro%20project%20/trends")
        insights = client.get(
            "/api/v1/projects/%20METRO%20PROJECT%20/insights"
        )
        schedule = client.get(
            "/api/v1/projects/%20METRO%20PROJECT%20/schedule-impact"
        )
        schedule_history = client.get(
            "/api/v1/projects/%20metro%20project%20/schedule-impact/history"
        )
        issue_history = client.get(
            "/api/v1/projects/%20METRO%20PROJECT%20/issues/history"
        )

    assert projects.json() == {"projects": ["Metro Project"]}
    assert trends.status_code == 200
    assert insights.status_code == 200
    assert insights.json()["project_name"] == "Metro Project"
    assert schedule.status_code == 200
    assert schedule.json()["project_name"] == "Metro Project"
    assert schedule_history.status_code == 200
    assert schedule_history.json()["project_name"] == "Metro Project"
    assert issue_history.status_code == 200
    assert issue_history.json()["project_name"] == "Metro Project"


def test_upload_records_extracted_report_once(tmp_path, monkeypatch):
    upload_module = importlib.import_module("app.api.upload")
    app.state.analysis_service = AnalysisService()
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(
        upload_module,
        "process_file",
        lambda file_path: {
            "extracted_data": _report().model_dump()
        },
    )

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/upload",
            files={"file": ("report.pdf", b"report")},
        )
        second = client.post(
            "/api/v1/upload",
            files={"file": ("report.pdf", b"report")},
        )
        history = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/history"
        )

    assert first.status_code == 201
    assert second.status_code == 201
    assert history.status_code == 200
    assert len(history.json()["snapshots"]) == 1
