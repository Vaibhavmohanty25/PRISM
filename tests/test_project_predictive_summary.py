from collections import Counter

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project_data import (
    ActivityProgress,
    DecisionSupport,
    ForecastConfidence,
    ForecastResult,
    PredictiveRisk,
    ProgressReport,
)
from app.services.analysis_service import AnalysisService


def _record(
    service: AnalysisService,
    *,
    activity_name: str,
    progress: float,
    report_date: str,
    project_name: str = "Metro Project",
) -> None:
    service.record_report(
        ProgressReport(
            project_name=project_name,
            report_date=report_date,
            activities=[
                ActivityProgress(
                    activity_name=activity_name,
                    progress_percentage=progress,
                )
            ],
        )
    )


def _forecast(
    activity_name: str,
    *,
    status: str = "available",
    progress: float = 50,
    confidence_status: str = "assessed",
    confidence_level: str | None = "high",
    predictive_level: str | None = "low",
) -> ForecastResult:
    confidence = ForecastConfidence(
        assessment_status=confidence_status,
        level=(
            confidence_level
            if confidence_status == "assessed"
            else None
        ),
        total_snapshot_count=2,
        usable_observation_count=2,
        missing_progress_count=0,
        interval_count=1,
        valid_velocity_interval_count=1,
        zero_day_gap_count=0,
        positive_interval_count=1,
        zero_interval_count=0,
        negative_interval_count=0,
        velocity_stability="stable",
        direction_consistency="positive",
        date_quality="complete",
        data_note=(
            "Confidence evidence was not assessed."
            if confidence_status != "assessed"
            else None
        ),
    )
    predictive_risk = (
        PredictiveRisk(
            project_name="Metro Project",
            activity_name=activity_name,
            level=predictive_level,
            data_note=(
                "Predictive risk was not assessed."
                if predictive_level == "not_assessed"
                else None
            ),
        )
        if predictive_level is not None
        else None
    )
    return ForecastResult(
        project_name="Metro Project",
        activity_name=activity_name,
        status=status,
        current_progress=progress,
        observation_count=2,
        forecast_method="net_observed_progress_velocity",
        confidence=confidence,
        predictive_risk=predictive_risk,
    )


def test_unknown_project_returns_no_summary():
    assert AnalysisService().analyze_project_predictive_summary(
        "Unknown Project"
    ) is None


def test_single_activity_summary_uses_typed_distributions():
    service = AnalysisService()
    _record(service, activity_name="Foundation", progress=30, report_date="1 June 2025")
    _record(service, activity_name="Foundation", progress=50, report_date="2 June 2025")

    result = service.analyze_project_predictive_summary("Metro Project")

    assert result is not None
    assert result.total_activity_count == 1
    assert result.active_activity_count == 1
    assert result.completed_activity_count == 0
    assert result.forecast_status_distribution.available == 1
    assert result.forecast_status_distribution.insufficient_data == 0
    assert result.forecast_status_distribution.unavailable == 0
    assert result.confidence_level_distribution.low == 1
    assert result.confidence_level_distribution.medium == 0
    assert result.confidence_level_distribution.high == 0
    assert result.predictive_risk_distribution.not_assessed == 1
    assert result.decision_support_status_distribution.insufficient_evidence == 1
    assert result.decision_support_priority_distribution.none == 1


def test_project_summary_preserves_tracker_order_and_canonical_aliases():
    service = AnalysisService()
    _record(service, activity_name="Zinc work", progress=20, report_date="1 June 2025")
    _record(service, activity_name="Zinc work", progress=30, report_date="2 June 2025")
    _record(service, activity_name="Brick work", progress=20, report_date="1 June 2025")
    _record(service, activity_name="Brick work", progress=30, report_date="2 June 2025")

    result = service.analyze_project_predictive_summary(" metro project ")

    assert result is not None
    assert [
        item.activity_name for item in result.activities_with_insufficient_evidence
    ] == ["Brick work", "Zinc work"]


def test_duplicate_reports_do_not_change_summary():
    service = AnalysisService()
    first = ProgressReport(
        project_name="Metro Project",
        report_date="1 June 2025",
        activities=[ActivityProgress(activity_name="Foundation", progress_percentage=30)],
    )
    second = ProgressReport(
        project_name="Metro Project",
        report_date="2 June 2025",
        activities=[ActivityProgress(activity_name="Foundation", progress_percentage=50)],
    )
    service.record_report(first)
    service.record_report(second)
    before = service.analyze_project_predictive_summary("Metro Project")
    service.record_report(second)
    after = service.analyze_project_predictive_summary("Metro Project")

    assert before == after


def test_mixed_activity_results_are_aggregated_without_reclassifying_them(monkeypatch):
    service = AnalysisService()
    activity_names = ["Available", "Insufficient", "Unavailable"]
    for name in activity_names:
        _record(service, activity_name=name, progress=40, report_date="1 June 2025")

    results = {
        "Available": _forecast("Available", confidence_level="high", predictive_level="low"),
        "Insufficient": _forecast(
            "Insufficient",
            status="insufficient_data",
            confidence_status="not_assessed",
            confidence_level=None,
            predictive_level="not_assessed",
        ),
        "Unavailable": _forecast(
            "Unavailable",
            status="unavailable",
            confidence_status="not_assessed",
            confidence_level=None,
            predictive_level="high",
        ),
    }
    calls = Counter()

    def forecast(project_name, activity_name):
        calls[activity_name] += 1
        return results[activity_name]

    monkeypatch.setattr(service, "analyze_activity_forecast", forecast)

    result = service.analyze_project_predictive_summary("Metro Project")

    assert result is not None
    assert result.forecast_status_distribution.available == 1
    assert result.forecast_status_distribution.insufficient_data == 1
    assert result.forecast_status_distribution.unavailable == 1
    assert result.confidence_level_distribution.high == 1
    assert result.confidence_level_distribution.not_assessed == 2
    assert result.predictive_risk_distribution.low == 1
    assert result.predictive_risk_distribution.high == 1
    assert result.predictive_risk_distribution.not_assessed == 1
    assert [
        item.activity_name for item in result.activities_requiring_attention
    ] == ["Unavailable", "Available", "Insufficient"]
    assert calls == Counter(dict.fromkeys(activity_names, 1))


def test_decision_support_response_is_authoritative_for_attention(monkeypatch):
    service = AnalysisService()
    names = ["Verify available", "High investigate", "Low monitor"]
    for name in names:
        _record(service, activity_name=name, progress=40, report_date="1 June 2025")

    forecasts = {
        "Verify available": _forecast("Verify available", predictive_level="low"),
        "High investigate": _forecast("High investigate", predictive_level="high"),
        "Low monitor": _forecast("Low monitor", predictive_level="low"),
    }
    decisions = {
        "Verify available": DecisionSupport(
            project_name="Metro Project", activity_name="Verify available",
            status="insufficient_evidence", priority="none", response="verify_data",
            trigger="data_quality", rationale="verify", limitations=["missing"],
        ),
        "High investigate": DecisionSupport(
            project_name="Metro Project", activity_name="High investigate",
            status="supported", priority="high", response="investigate",
            trigger="predictive_risk", rationale="investigate", limitations=[],
        ),
        "Low monitor": DecisionSupport(
            project_name="Metro Project", activity_name="Low monitor",
            status="supported", priority="low", response="monitor",
            trigger="observed_risk", rationale="monitor", limitations=[],
        ),
    }
    monkeypatch.setattr(
        service,
        "analyze_activity_forecast",
        lambda project_name, activity_name: forecasts[activity_name],
    )
    monkeypatch.setattr(
        service.decision_support_analyzer,
        "analyze",
        lambda trend, risk, forecast, schedule, issue: decisions[trend.activity_name],
    )

    result = service.analyze_project_predictive_summary("Metro Project")

    assert result is not None
    assert [item.activity_name for item in result.activities_requiring_attention] == [
        "High investigate",
        "Verify available",
    ]
    assert "Low monitor" not in {
        item.activity_name for item in result.activities_requiring_attention
    }


def test_completed_activity_is_counted_but_excluded_from_attention_and_limitations():
    service = AnalysisService()
    _record(service, activity_name="Completed", progress=80, report_date="1 June 2025")
    _record(service, activity_name="Completed", progress=100, report_date="2 June 2025")
    _record(service, activity_name="Active", progress=40, report_date="1 June 2025")

    result = service.analyze_project_predictive_summary("Metro Project")

    assert result is not None
    assert result.total_activity_count == 2
    assert result.active_activity_count == 1
    assert result.completed_activity_count == 1
    assert result.forecast_status_distribution.available == 1
    assert result.forecast_status_distribution.insufficient_data == 1
    assert result.confidence_level_distribution.not_applicable == 1
    assert result.predictive_risk_distribution.not_applicable == 1
    assert result.decision_support_status_distribution.not_applicable == 1
    assert result.decision_support_priority_distribution.none == 2
    assert [item.activity_name for item in result.activities_requiring_attention] == [
        "Active"
    ]
    assert "Completed" not in {
        item.activity_name
        for item in result.activities_with_insufficient_evidence
    }


def test_attention_order_is_priority_response_risk_then_name(monkeypatch):
    service = AnalysisService()
    names = ["Medium review", "High investigate", "Low verify"]
    for name in names:
        _record(service, activity_name=name, progress=40, report_date="1 June 2025")

    decisions = {
        "Medium review": DecisionSupport(
            project_name="Metro Project", activity_name="Medium review",
            status="review_only", priority="medium", response="review",
            trigger="predictive_risk", rationale="review", limitations=[],
        ),
        "High investigate": DecisionSupport(
            project_name="Metro Project", activity_name="High investigate",
            status="supported", priority="high", response="investigate",
            trigger="combined_evidence", rationale="investigate", limitations=[],
        ),
        "Low verify": DecisionSupport(
            project_name="Metro Project", activity_name="Low verify",
            status="insufficient_evidence", priority="none", response="verify_data",
            trigger="data_quality", rationale="verify", limitations=["missing"],
        ),
    }

    monkeypatch.setattr(
        service.decision_support_analyzer,
        "analyze",
        lambda trend, risk, forecast, schedule, issue: decisions[trend.activity_name],
    )

    result = service.analyze_project_predictive_summary("Metro Project")

    assert result is not None
    assert [item.activity_name for item in result.activities_requiring_attention] == [
        "High investigate",
        "Medium review",
        "Low verify",
    ]


def test_missing_activity_forecast_is_explicitly_insufficient(monkeypatch):
    service = AnalysisService()
    _record(service, activity_name="Missing forecast", progress=40, report_date="1 June 2025")
    monkeypatch.setattr(service, "analyze_activity_forecast", lambda *_: None)

    result = service.analyze_project_predictive_summary("Metro Project")

    assert result is not None
    assert result.forecast_status_distribution.unavailable == 1
    assert result.predictive_risk_distribution.not_assessed == 1
    assert result.predictive_risk_distribution.low == 0
    assert result.predictive_risk_distribution.high == 0
    assert [item.activity_name for item in result.activities_with_insufficient_evidence] == [
        "Missing forecast"
    ]
    assert [item.activity_name for item in result.activities_requiring_attention] == [
        "Missing forecast"
    ]
    assert any("forecast" in item.lower() for item in result.evidence_limitations)


def test_low_confidence_does_not_downgrade_high_predictive_risk(monkeypatch):
    service = AnalysisService()
    _record(service, activity_name="Unstable", progress=40, report_date="1 June 2025")
    monkeypatch.setattr(
        service,
        "analyze_activity_forecast",
        lambda *_: _forecast(
            "Unstable",
            confidence_level="low",
            predictive_level="high",
        ),
    )
    monkeypatch.setattr(
        service.decision_support_analyzer,
        "analyze",
        lambda *args: DecisionSupport(
            project_name="Metro Project",
            activity_name="Unstable",
            status="supported",
            priority="high",
            response="investigate",
            trigger="predictive_risk",
            rationale="investigate",
            limitations=["low confidence"],
        ),
    )

    result = service.analyze_project_predictive_summary("Metro Project")

    assert result is not None
    assert result.confidence_level_distribution.low == 1
    assert result.predictive_risk_distribution.high == 1
    assert result.predictive_risk_distribution.medium == 0
    assert result.predictive_risk_distribution.low == 0


def test_summary_has_no_project_risk_score_or_prediction_fields():
    fields = set(AnalysisService().analyze_project_predictive_summary.__annotations__)
    assert "risk_score" not in fields


def test_predictive_summary_endpoint_and_openapi_contract():
    app.state.analysis_service = AnalysisService()
    _record(app.state.analysis_service, activity_name="Foundation", progress=40, report_date="1 June 2025")

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/projects/%20METRO%20PROJECT%20/predictive-summary"
        )
        unknown = client.get(
            "/api/v1/projects/Unknown%20Project/predictive-summary"
        )
        schema = client.get("/openapi.json").json()

    assert response.status_code == 200
    assert response.json()["project_name"] == "Metro Project"
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "project_not_found"
    assert schema["paths"][
        "/api/v1/projects/{project_name}/predictive-summary"
    ]["get"]["responses"]["200"]["content"]
    components = schema["components"]["schemas"]
    assert "ProjectPredictiveSummary" in components
    assert "ProjectPredictiveActivity" in components
    assert "ForecastStatusDistribution" in components
    assert "ConfidenceLevelDistribution" in components
    assert "PredictiveRiskDistribution" in components
    assert "DecisionSupportStatusDistribution" in components
    assert "DecisionSupportPriorityDistribution" in components
    properties = components["ProjectPredictiveSummary"]["properties"]
    for prohibited in {
        "risk_score",
        "estimated_completion_date",
        "probability",
        "project_risk",
        "project_completion",
        "critical_path",
        "dependencies",
        "dependency_graph",
    }:
        assert prohibited not in properties
    assert set(components["ForecastStatusDistribution"]["properties"]) == {
        "available", "insufficient_data", "unavailable"
    }
    assert set(components["ConfidenceLevelDistribution"]["properties"]) == {
        "high", "medium", "low", "not_assessed", "not_applicable"
    }
    assert set(components["PredictiveRiskDistribution"]["properties"]) == {
        "low", "medium", "high", "not_assessed", "not_applicable"
    }
    assert set(components["DecisionSupportStatusDistribution"]["properties"]) == {
        "supported", "review_only", "insufficient_evidence", "not_applicable"
    }
    assert set(components["DecisionSupportPriorityDistribution"]["properties"]) == {
        "none", "low", "medium", "high"
    }
