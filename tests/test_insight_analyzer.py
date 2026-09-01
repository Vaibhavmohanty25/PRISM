from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService


def _record_reports(
    service: AnalysisService,
    *,
    activity_name: str,
    entries: list[tuple[str | None, float | None, str | None, list[str]]],
) -> None:
    for report_date, progress, delay_reason, issues in entries:
        service.record_report(
            ProgressReport(
                project_name="Metro Project",
                report_date=report_date,
                activities=[
                    ActivityProgress(
                        activity_name=activity_name,
                        progress_percentage=progress,
                        delay_reason=delay_reason,
                        issues=issues,
                    )
                ],
            )
        )


def test_declining_progress_has_high_priority_and_recommendation():
    service = AnalysisService()
    _record_reports(
        service,
        activity_name="Foundation RCC work",
        entries=[
            ("1 June 2025", 60, None, []),
            ("8 June 2025", 50, None, []),
        ],
    )

    result = service.analyze_activity_insight(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.status == "available"
    assert result.risk_level == "high"
    assert result.risk_score == 80
    assert [(finding.finding_type, finding.priority) for finding in result.findings] == [
        ("declining_progress", "high"),
        ("low_velocity", "medium"),
    ]
    finding = result.findings[0]
    assert finding.factual_evidence == [
        "Progress changed from 60% to 50% across the available history."
    ]
    assert finding.recommendation is not None


def test_multiple_findings_keep_independent_explicit_priorities():
    service = AnalysisService()
    _record_reports(
        service,
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 50, "Heavy rainfall", ["Material shortage"]),
            ("12 June 2025", 50.5, "heavy rainfall", ["material shortage"]),
        ],
    )

    result = service.analyze_activity_insight(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.risk_level == "high"
    assert result.risk_score == 75
    assert [finding.finding_type for finding in result.findings] == [
        "stalled_activity",
        "low_velocity",
        "repeated_delay",
        "repeated_issue",
    ]
    assert [finding.priority for finding in result.findings] == [
        "medium",
        "medium",
        "medium",
        "medium",
    ]
    assert all(
        finding.factual_evidence and finding.recommendation
        for finding in result.findings
    )


def test_repeated_findings_are_sorted_deterministically():
    service = AnalysisService()
    _record_reports(
        service,
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 35, "Equipment failure", ["Waterlogging"]),
            ("12 June 2025", 40, "Heavy rainfall", ["Material shortage"]),
            ("19 June 2025", 45, "equipment failure", ["material shortage"]),
            ("26 June 2025", 50, "heavy rainfall", ["waterlogging"]),
        ],
    )

    result = service.analyze_activity_insight(
        "Metro Project",
        "Foundation RCC work",
    )

    assert [
        (finding.finding_type, finding.title)
        for finding in result.findings
    ] == [
        ("repeated_delay", "Repeated delay: Equipment failure"),
        ("repeated_delay", "Repeated delay: Heavy rainfall"),
        ("repeated_issue", "Repeated issue: Material shortage"),
        ("repeated_issue", "Repeated issue: Waterlogging"),
    ]


def test_insufficient_history_returns_typed_insight():
    service = AnalysisService()
    _record_reports(
        service,
        activity_name="Foundation RCC work",
        entries=[("5 June 2025", 70, None, [])],
    )

    result = service.analyze_activity_insight(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.status == "insufficient_data"
    assert result.risk_level == "insufficient_data"
    assert result.risk_score == 0
    assert result.trend == "insufficient_data"
    assert result.findings == []
    assert result.data_note == (
        "At least two usable progress observations are required to produce findings."
    )


def test_project_insights_preserve_stable_activity_order():
    service = AnalysisService()
    _record_reports(
        service,
        activity_name="Zinc work",
        entries=[("1 June 2025", 10, None, [])],
    )
    _record_reports(
        service,
        activity_name="Brick masonry work",
        entries=[("1 June 2025", 10, None, [])],
    )

    result = service.analyze_project_insight("Metro Project")

    assert [activity.activity_name for activity in result.activities] == [
        "Brick masonry work",
        "Zinc work",
    ]


def test_insight_endpoints_return_typed_results_and_404s():
    app.state.analysis_service = AnalysisService()
    service = app.state.analysis_service
    _record_reports(
        service,
        activity_name="Foundation RCC work",
        entries=[
            ("1 June 2025", 60, None, []),
            ("8 June 2025", 50, None, []),
        ],
    )

    with TestClient(app) as client:
        project_response = client.get(
            "/api/v1/projects/Metro%20Project/insights"
        )
        activity_response = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Foundation%20RCC%20work/insight"
        )
        unknown_project = client.get(
            "/api/v1/projects/Unknown%20Project/insights"
        )
        unknown_activity = client.get(
            "/api/v1/projects/Metro%20Project/activities/"
            "Unknown%20work/insight"
        )

    assert project_response.status_code == 200
    assert project_response.json()["activities"][0]["findings"][0][
        "finding_type"
    ] == "declining_progress"
    assert activity_response.status_code == 200
    assert activity_response.json()["risk_level"] == "high"
    assert unknown_project.status_code == 404
    assert unknown_activity.status_code == 404
