import pytest

from app.schemas.project_data import (
    ForecastConfidence,
    ForecastResult,
)
from app.services.predictive_risk_analyzer import PredictiveRiskAnalyzer


def _confidence(
    *,
    direction="positive",
    stability="stable",
    assessment_status="assessed",
    level=None,
    date_quality="complete",
    valid_velocity_interval_count=1,
    missing_progress_count=0,
    zero_day_gap_count=0,
):
    return ForecastConfidence(
        assessment_status=assessment_status,
        level=(
            level
            if level is not None
            else ("low" if assessment_status == "assessed" else None)
        ),
        total_snapshot_count=2,
        usable_observation_count=2,
        missing_progress_count=missing_progress_count,
        interval_count=1,
        valid_velocity_interval_count=valid_velocity_interval_count,
        zero_day_gap_count=zero_day_gap_count,
        positive_interval_count=1 if direction == "positive" else 0,
        zero_interval_count=1 if direction == "non_positive" else 0,
        negative_interval_count=1 if direction == "non_positive" else 0,
        velocity_stability=stability,
        direction_consistency=direction,
        date_quality=date_quality,
    )


def _forecast(
    *,
    status="available",
    current_progress=50,
    historical_velocity=1.0,
    confidence=None,
):
    return ForecastResult(
        project_name="Metro Project",
        activity_name="Foundation",
        status=status,
        current_progress=current_progress,
        historical_velocity_per_day=historical_velocity,
        observation_count=2,
        forecast_method="net_observed_progress_velocity",
        confidence=confidence,
    )


@pytest.mark.parametrize(
    ("direction", "stability", "expected"),
    [
        ("positive", "stable", "low"),
        ("positive", "variable", "medium"),
        ("positive", "unstable", "medium"),
        ("mixed", "stable", "medium"),
        ("mixed", "variable", "medium"),
        ("mixed", "unstable", "high"),
        ("non_positive", "stable", "high"),
    ],
)
def test_locked_trajectory_decision_table(direction, stability, expected):
    forecast = _forecast(
        confidence=_confidence(
            direction=direction,
            stability=stability,
        )
    )

    result = PredictiveRiskAnalyzer().analyze(forecast)

    assert result.level == expected


def test_completed_activity_is_not_applicable():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            current_progress=100,
            confidence=None,
        )
    )

    assert result.level == "not_applicable"
    assert result.evidence == [
        "Activity is complete at 100% observed progress."
    ]


@pytest.mark.parametrize("current_progress", [-1, 101])
def test_out_of_range_progress_is_not_assessed(current_progress):
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(current_progress=current_progress)
    )

    assert result.level == "not_assessed"


def test_missing_confidence_is_not_assessed():
    result = PredictiveRiskAnalyzer().analyze(_forecast(confidence=None))

    assert result.level == "not_assessed"


def test_insufficient_forecast_is_not_assessed():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            status="insufficient_data",
            confidence=_confidence(assessment_status="not_assessed"),
        )
    )

    assert result.level == "not_assessed"


def test_unavailable_non_positive_forecast_is_high():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            status="unavailable",
            historical_velocity=0,
            confidence=_confidence(
                direction="non_positive",
                stability="not_assessable",
                assessment_status="not_assessed",
            ),
        )
    )

    assert result.level == "high"


def test_unavailable_unusable_dates_are_not_assessed():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            status="unavailable",
            historical_velocity=None,
            confidence=_confidence(
                direction="not_assessable",
                stability="not_assessable",
                assessment_status="not_assessed",
                date_quality="unusable",
                valid_velocity_interval_count=0,
            ),
        )
    )

    assert result.level == "not_assessed"


def test_unavailable_with_not_assessable_direction_is_not_assessed():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            status="unavailable",
            historical_velocity=None,
            confidence=_confidence(
                direction="not_assessable",
                stability="not_assessable",
                assessment_status="not_assessed",
                date_quality="submission_order_fallback",
                valid_velocity_interval_count=0,
            ),
        )
    )

    assert result.level == "not_assessed"


@pytest.mark.parametrize("direction", ["positive", "mixed"])
def test_not_assessable_stability_is_not_assessed(direction):
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            confidence=_confidence(
                direction=direction,
                stability="not_assessable",
            )
        )
    )

    assert result.level == "not_assessed"


def test_non_positive_not_assessable_stability_is_high_when_velocity_is_non_positive():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            status="unavailable",
            historical_velocity=-1,
            confidence=_confidence(
                direction="non_positive",
                stability="not_assessable",
                assessment_status="not_assessed",
            ),
        )
    )

    assert result.level == "high"


def test_non_positive_not_assessable_stability_is_not_assessed_when_velocity_is_positive():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            historical_velocity=1,
            confidence=_confidence(
                direction="non_positive",
                stability="not_assessable",
            ),
        )
    )

    assert result.level == "not_assessed"


def test_missing_progress_does_not_raise_healthy_trajectory_risk():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            confidence=_confidence(
                missing_progress_count=1,
                direction="positive",
                stability="stable",
            )
        )
    )

    assert result.level == "low"
    assert any("lacked usable progress" in item for item in result.evidence)


def test_confidence_level_does_not_change_predictive_risk():
    low_confidence = _forecast(
        confidence=_confidence(
            direction="positive",
            stability="stable",
            level="low",
        )
    )
    high_confidence = _forecast(
        confidence=_confidence(
            direction="positive",
            stability="stable",
            level="high",
        )
    )

    analyzer = PredictiveRiskAnalyzer()

    assert analyzer.analyze(low_confidence).level == "low"
    assert analyzer.analyze(high_confidence).level == "low"


def test_same_day_interval_with_valid_interval_uses_valid_trajectory():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            confidence=_confidence(
                direction="positive",
                stability="stable",
                zero_day_gap_count=1,
            )
        )
    )

    assert result.level == "low"


def test_all_same_day_intervals_are_not_assessed():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            confidence=_confidence(
                direction="not_assessable",
                stability="not_assessable",
                date_quality="unusable",
                valid_velocity_interval_count=0,
                zero_day_gap_count=1,
            )
        )
    )

    assert result.level == "not_assessed"


def test_negative_day_gap_fallback_without_valid_trajectory_is_not_assessed():
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            status="unavailable",
            historical_velocity=None,
            confidence=_confidence(
                direction="not_assessable",
                stability="not_assessable",
                assessment_status="not_assessed",
                date_quality="submission_order_fallback",
                valid_velocity_interval_count=0,
            ),
        )
    )

    assert result.level == "not_assessed"


@pytest.mark.parametrize(
    "date_quality",
    ["submission_order_fallback", "unusable"],
)
def test_unusable_temporal_evidence_is_not_assessed(date_quality):
    result = PredictiveRiskAnalyzer().analyze(
        _forecast(
            status="unavailable",
            historical_velocity=None,
            confidence=_confidence(
                direction="not_assessable",
                stability="not_assessable",
                assessment_status="not_assessed",
                date_quality=date_quality,
                valid_velocity_interval_count=0,
            ),
        )
    )

    assert result.level == "not_assessed"


def test_repeated_calls_and_evidence_order_are_deterministic():
    forecast = _forecast(
        confidence=_confidence(
            direction="mixed",
            stability="variable",
            missing_progress_count=1,
        )
    )

    analyzer = PredictiveRiskAnalyzer()
    first = analyzer.analyze(forecast)
    second = analyzer.analyze(forecast)

    assert first == second
    assert first.evidence == [
        "Observed trajectory contains both positive and non-positive progress movement.",
        "Observed progress velocity is variable.",
        "Some progress snapshots lacked usable progress and were excluded from trajectory evidence.",
    ]


def test_analyzer_does_not_mutate_forecast_or_confidence():
    forecast = _forecast(
        confidence=_confidence(
            direction="positive",
            stability="stable",
        )
    )
    before = forecast.model_dump()

    PredictiveRiskAnalyzer().analyze(forecast)

    assert forecast.model_dump() == before
