import pytest

from app.schemas.project_data import (
    ActivityIssueHistory,
    ActivityScheduleImpact,
    ForecastConfidence,
    ForecastResult,
    IssueObservation,
    PredictiveRisk,
    RiskResult,
    TrendResult,
)
from app.services.decision_support_analyzer import DecisionSupportAnalyzer


def _trend(*, trend="improving", snapshot_count=2):
    return TrendResult(
        project_name="Metro Project",
        activity_name="Foundation",
        trend=trend,
        snapshot_count=snapshot_count,
    )


def _risk(*, level="low", repeated_delays=None, repeated_issues=None):
    return RiskResult(
        project_name="Metro Project",
        activity_name="Foundation",
        risk_level=level,
        risk_score=80 if level == "high" else 30 if level == "medium" else 0,
        risk_signals=[f"Observed risk is {level}."],
        repeated_delays=repeated_delays or [],
        repeated_issues=repeated_issues or [],
        trend="improving",
        snapshot_count=2,
    )


def _confidence(*, level="high", assessment_status="assessed"):
    return ForecastConfidence(
        assessment_status=assessment_status,
        level=level if assessment_status == "assessed" else None,
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
    )


def _forecast(*, progress=50, predictive="low", confidence="high"):
    return ForecastResult(
        project_name="Metro Project",
        activity_name="Foundation",
        status="available",
        current_progress=progress,
        observation_count=2,
        forecast_method="net_observed_progress_velocity",
        confidence=_confidence(level=confidence)
        if confidence is not None
        else None,
        predictive_risk=(
            PredictiveRisk(
                project_name="Metro Project",
                activity_name="Foundation",
                level=predictive,
                evidence=[f"Predictive risk is {predictive}."],
            )
            if predictive is not None
            else None
        ),
    )


def _schedule(*, status="insufficient_data", count=0, repeated=None):
    return ActivityScheduleImpact(
        project_name="Metro Project",
        activity_name="Foundation",
        status=status,
        delay_observation_count=count,
        repeated_delay_reasons=repeated or [],
        progress_trend="improving",
        summary="Observed delay information was reported." if count else "No delay data.",
    )


def _issues(*values):
    return ActivityIssueHistory(
        project_name="Metro Project",
        activity_name="Foundation",
        observations=[
            IssueObservation(issue=value, submission_order=index)
            for index, value in enumerate(values, start=1)
        ],
    )


def _analyze(
    *,
    trend=None,
    risk=None,
    forecast=None,
    schedule=None,
    issues=None,
):
    return DecisionSupportAnalyzer().analyze(
        trend or _trend(),
        risk,
        forecast,
        schedule or _schedule(),
        issues or ActivityIssueHistory(
            project_name="Metro Project",
            activity_name="Foundation",
        ),
    )


def test_completion_is_not_applicable():
    result = _analyze(forecast=_forecast(progress=100))

    assert (result.status, result.priority, result.response, result.trigger) == (
        "not_applicable",
        "none",
        "none",
        "completion",
    )


@pytest.mark.parametrize(
    ("predictive", "expected_trigger"),
    [("low", "observed_risk"), (None, "observed_risk")],
)
def test_high_observed_risk_remains_investigate(
    predictive, expected_trigger
):
    result = _analyze(
        risk=_risk(level="high"),
        forecast=_forecast(predictive=predictive),
    )

    assert (result.status, result.priority, result.response) == (
        "supported",
        "high",
        "investigate",
    )
    assert result.trigger == expected_trigger


def test_high_observed_and_high_predictive_use_combined_trigger():
    result = _analyze(
        risk=_risk(level="high"),
        forecast=_forecast(predictive="high"),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "supported",
        "high",
        "investigate",
        "combined_evidence",
    )


@pytest.mark.parametrize("confidence", ["low", "medium", None])
def test_high_predictive_is_not_downgraded_by_confidence(confidence):
    forecast = _forecast(predictive="high", confidence=confidence)
    if confidence is None:
        forecast.confidence = _confidence(
            level=None,
            assessment_status="not_assessed",
        )

    result = _analyze(risk=_risk(level="low"), forecast=forecast)

    assert (result.status, result.priority, result.response, result.trigger) == (
        "supported",
        "high",
        "review",
        "predictive_risk",
    )
    assert result.limitations


def test_medium_observed_and_high_predictive_preserves_high_predictive_classification():
    result = _analyze(
        risk=_risk(level="medium"),
        forecast=_forecast(predictive="high"),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "supported",
        "high",
        "review",
        "predictive_risk",
    )


@pytest.mark.parametrize(
    ("risk_level", "predictive", "trigger"),
    [
        ("medium", "low", "observed_risk"),
        ("low", "medium", "predictive_risk"),
    ],
)
def test_medium_signal_is_review_only(risk_level, predictive, trigger):
    result = _analyze(
        risk=_risk(level=risk_level),
        forecast=_forecast(predictive=predictive),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "review_only",
        "medium",
        "review",
        trigger,
    )


def test_low_signals_without_explicit_triggers_monitor():
    result = _analyze(
        risk=_risk(level="low"),
        forecast=_forecast(predictive="low"),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "supported",
        "low",
        "monitor",
        "observed_risk",
    )


def test_repeated_issue_evidence_is_medium_investigate_without_changing_predictive_risk():
    result = _analyze(
        risk=_risk(level="low"),
        forecast=_forecast(predictive="low"),
        issues=_issues("Access blocked", "Access blocked"),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "review_only",
        "medium",
        "investigate",
        "issue_evidence",
    )
    assert result.trigger != "predictive_risk"


def test_repeated_issue_from_risk_result_is_authoritative_without_issue_history():
    result = _analyze(
        risk=_risk(level="low", repeated_issues=["Access blocked"]),
        forecast=_forecast(predictive="low"),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "review_only",
        "medium",
        "investigate",
        "issue_evidence",
    )
    assert any("Access blocked" in item for item in result.evidence)


def test_isolated_issue_or_delay_is_low_review():
    result = _analyze(
        risk=_risk(level="low"),
        forecast=_forecast(predictive="low"),
        issues=_issues("Access blocked"),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "review_only",
        "low",
        "review",
        "issue_evidence",
    )


def test_repeated_delay_evidence_is_medium_investigate():
    result = _analyze(
        risk=_risk(level="low"),
        forecast=_forecast(predictive="low"),
        schedule=_schedule(
            status="available",
            count=2,
            repeated=["Heavy rainfall"],
        ),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "review_only",
        "medium",
        "investigate",
        "issue_evidence",
    )


def test_schedule_impact_alone_is_medium_review_without_slippage_claim():
    result = _analyze(
        risk=_risk(level="low"),
        forecast=_forecast(predictive="low"),
        schedule=_schedule(status="available", count=1),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "review_only",
        "medium",
        "review",
        "schedule_impact",
    )
    assert all("slippage" not in item.lower() for item in result.evidence)


def test_insufficient_evidence_requests_data_verification():
    result = _analyze(
        risk=_risk(level="insufficient_data"),
        forecast=_forecast(predictive="not_assessed", confidence=None),
    )

    assert (result.status, result.priority, result.response, result.trigger) == (
        "insufficient_evidence",
        "none",
        "verify_data",
        "data_quality",
    )


def test_evidence_order_is_deterministic_and_inputs_are_not_mutated():
    inputs = {
        "trend_result": _trend(),
        "risk_result": _risk(level="medium", repeated_issues=["Access blocked"]),
        "forecast_result": _forecast(predictive="medium", confidence="low"),
        "schedule_impact": _schedule(status="available", count=1),
        "issue_history": _issues("Access blocked"),
    }
    before = {name: value.model_dump() for name, value in inputs.items()}
    analyzer = DecisionSupportAnalyzer()

    first = analyzer.analyze(**inputs)
    second = analyzer.analyze(**inputs)

    assert first == second
    assert first.model_dump() == second.model_dump()
    assert {name: value.model_dump() for name, value in inputs.items()} == before
