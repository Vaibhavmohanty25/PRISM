from datetime import date

import pytest

from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.forecast_analyzer import ForecastAnalyzer
from app.services.progress_tracker import ProgressTracker
from app.services.risk_analyzer import RiskAnalyzer
from app.services.trend_analyzer import TrendAnalyzer


def _record(
    entries: list[tuple[str | None, float | None]],
    *,
    project_name: str = "Metro Project",
    activity_name: str = "Foundation RCC work",
    delay_reason: str | None = None,
    delay_duration_hours: float | None = None,
    issues: list[str] | None = None,
) -> tuple[ProgressTracker, ForecastAnalyzer]:
    tracker = ProgressTracker()

    for report_date, progress in entries:
        tracker.record(
            ProgressReport(
                project_name=project_name,
                report_date=report_date,
                activities=[
                    ActivityProgress(
                        activity_name=activity_name,
                        progress_percentage=progress,
                        delay_reason=delay_reason,
                        delay_duration_hours=delay_duration_hours,
                        issues=issues or [],
                    )
                ],
            )
        )

    return tracker, ForecastAnalyzer(tracker)


def test_basic_forecast_calculates_remaining_progress_duration_and_date():
    tracker, analyzer = _record(
        [("1 June 2025", 35), ("15 June 2025", 57)]
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.status == "available"
    assert result.current_progress == 57
    assert result.remaining_progress == 43
    assert result.historical_velocity_per_day == 22 / 14
    assert result.estimated_days_to_completion == 43 / (22 / 14)
    assert result.estimated_completion_date == "2025-07-12"
    assert result.observation_count == 2
    assert result.first_report_date == "1 June 2025"
    assert result.latest_report_date == "15 June 2025"
    assert result.forecast_method == "net_observed_progress_velocity"
    assert result.evidence


def test_out_of_order_ingestion_uses_phase2_chronological_order():
    _, analyzer = _record(
        [("15 June 2025", 20), ("1 June 2025", 10)]
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.current_progress == 20
    assert result.historical_velocity_per_day == 10 / 14
    assert result.latest_report_date == "15 June 2025"


def test_duplicate_report_does_not_change_forecast_observations():
    tracker, analyzer = _record(
        [("1 June 2025", 35), ("15 June 2025", 57)]
    )
    duplicate = ProgressReport(
        project_name="Metro Project",
        report_date="15 June 2025",
        activities=[
            ActivityProgress(
                activity_name="Foundation RCC work",
                progress_percentage=57,
            )
        ],
    )
    tracker.record(duplicate)

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.observation_count == 2
    assert result.historical_velocity_per_day == 22 / 14


def test_single_usable_progress_observation_is_insufficient_data():
    _, analyzer = _record([("1 June 2025", 70)])

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.status == "insufficient_data"
    assert result.current_progress == 70
    assert result.estimated_days_to_completion is None
    assert result.estimated_completion_date is None
    assert result.data_note


def test_multiple_snapshots_without_usable_progress_are_insufficient_data():
    _, analyzer = _record([("1 June 2025", None), ("15 June 2025", None)])

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.status == "insufficient_data"
    assert result.observation_count == 0


@pytest.mark.parametrize("progresses", [[50, 50], [60, 40]])
def test_zero_or_negative_velocity_is_unavailable(progresses):
    _, analyzer = _record(
        [("1 June 2025", progresses[0]), ("15 June 2025", progresses[1])]
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.status == "unavailable"
    assert result.historical_velocity_per_day <= 0
    assert result.estimated_completion_date is None
    assert result.data_note


def test_missing_report_dates_are_unavailable_without_fabricated_date():
    _, analyzer = _record([(None, 20), (None, 40)])

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.status == "unavailable"
    assert result.historical_velocity_per_day is None
    assert result.estimated_days_to_completion is None
    assert result.estimated_completion_date is None
    assert result.data_note


def test_malformed_and_mixed_dates_use_fallback_and_are_unavailable():
    _, analyzer = _record(
        [("15 June 2025", 20), ("not-a-date", 30), ("1 June 2025", 40)]
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.status == "unavailable"
    assert result.current_progress == 40
    assert result.latest_report_date == "1 June 2025"
    assert result.estimated_completion_date is None


def test_one_hundred_percent_progress_is_available_at_latest_date():
    _, analyzer = _record(
        [("1 June 2025", 80), ("15 June 2025", 100)]
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.status == "available"
    assert result.current_progress == 100
    assert result.remaining_progress == 0
    assert result.estimated_days_to_completion == 0
    assert result.estimated_completion_date == "2025-06-15"


def test_project_and_activity_aliases_resolve_to_canonical_history():
    _, analyzer = _record(
        [("1 June 2025", 35), ("15 June 2025", 57)],
        project_name="  Metro Project  ",
        activity_name=" Foundation RCC work ",
    )

    result = analyzer.analyze_activity(
        " METRO PROJECT ",
        "foundation rcc work",
    )

    assert result is not None
    assert result.project_name == "Metro Project"
    assert result.activity_name == "Foundation RCC work"


def test_delay_and_issue_fields_do_not_change_forecast():
    _, baseline = _record(
        [("1 June 2025", 35), ("15 June 2025", 57)]
    )
    _, with_evidence = _record(
        [("1 June 2025", 35), ("15 June 2025", 57)],
        delay_reason="Rain",
        delay_duration_hours=48,
        issues=["Access problem"],
    )

    baseline_result = baseline.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )
    evidence_result = with_evidence.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert baseline_result is not None
    assert evidence_result is not None
    assert evidence_result.model_dump() == baseline_result.model_dump()


def test_repeated_calls_are_deterministic_and_unknown_activity_is_none():
    _, analyzer = _record(
        [("1 June 2025", 35), ("15 June 2025", 57)]
    )

    first = analyzer.analyze_activity("Metro Project", "Foundation RCC work")
    second = analyzer.analyze_activity("Metro Project", "Foundation RCC work")

    assert first is not None
    assert first == second
    assert analyzer.analyze_activity("Metro Project", "Unknown") is None


def test_forecast_does_not_change_phase2_trend_or_risk_semantics():
    tracker, analyzer = _record(
        [("1 June 2025", 35), ("15 June 2025", 57)],
        delay_reason="Rain",
        delay_duration_hours=48,
        issues=["Access problem"],
    )

    forecast = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )
    trend = TrendAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )
    risk = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert forecast is not None
    assert trend is not None
    assert risk is not None
    assert trend.trend == "improving"
    assert trend.progress_deltas == [22.0]
    assert risk.trend == "improving"
    assert risk.risk_level == "medium"


def test_forecast_result_uses_original_report_date_strings_and_iso_date():
    _, analyzer = _record(
        [("05/06/2025", 50), ("2025-06-15", 60)]
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result is not None
    assert result.first_report_date == "05/06/2025"
    assert result.latest_report_date == "2025-06-15"
    date.fromisoformat(result.estimated_completion_date)
