import pytest

from app.schemas.project_data import (
    ActivityHistory,
    ActivityProgress,
    ActivitySnapshot,
    ForecastResult,
    ProgressReport,
)
from app.services.forecast_analyzer import ForecastAnalyzer
from app.services.forecast_confidence_analyzer import ForecastConfidenceAnalyzer
from app.services.progress_tracker import ProgressTracker


def _service(entries, *, delay=None, issues=None):
    tracker = ProgressTracker()
    for report_date, progress in entries:
        tracker.record(
            ProgressReport(
                project_name="Metro Project",
                report_date=report_date,
                activities=[
                    ActivityProgress(
                        activity_name="Foundation",
                        progress_percentage=progress,
                        delay_reason=delay,
                        delay_duration_hours=8 if delay else None,
                        issues=issues or [],
                    )
                ],
            )
        )
    return tracker


def _confidence(entries, **kwargs):
    tracker = _service(entries, **kwargs)
    history = tracker.get_activity_history("Metro Project", "Foundation")
    forecast = ForecastAnalyzer(tracker).analyze_activity(
        "Metro Project", "Foundation"
    )
    assert history is not None
    assert forecast is not None
    return ForecastConfidenceAnalyzer().analyze_history(history, forecast)


def test_two_observations_have_low_evidence_quality():
    result = _confidence([("1 June 2025", 10), ("2 June 2025", 20)])

    assert result.assessment_status == "assessed"
    assert result.level == "low"
    assert result.usable_observation_count == 2
    assert result.interval_count == 1


def test_three_stable_observations_are_medium_but_never_high():
    result = _confidence(
        [("1 June 2025", 10), ("2 June 2025", 20), ("3 June 2025", 30)]
    )

    assert result.level == "medium"
    assert result.velocity_stability == "stable"
    assert result.direction_consistency == "positive"


def test_five_stable_complete_positive_observations_can_be_high():
    result = _confidence(
        [
            ("1 June 2025", 10),
            ("2 June 2025", 20),
            ("3 June 2025", 30),
            ("4 June 2025", 40),
            ("5 June 2025", 50),
        ]
    )

    assert result.level == "high"
    assert result.velocity_stability == "stable"
    assert result.valid_velocity_interval_count == 4
    assert result.positive_interval_count == 4


def test_missing_progress_is_counted_and_caps_confidence():
    result = _confidence(
        [
            ("1 June 2025", 10),
            ("2 June 2025", None),
            ("3 June 2025", 20),
            ("4 June 2025", 30),
            ("5 June 2025", 40),
            ("6 June 2025", 50),
        ]
    )

    assert result.total_snapshot_count == 6
    assert result.usable_observation_count == 5
    assert result.missing_progress_count == 1
    assert result.level in {"low", "medium"}


def test_same_day_pair_is_retained_but_not_a_velocity_interval():
    result = _confidence(
        [("1 June 2025", 10), ("1 June 2025", 20), ("2 June 2025", 30)]
    )

    assert result.interval_count == 2
    assert result.valid_velocity_interval_count == 1
    assert result.zero_day_gap_count == 1
    assert result.velocity_stability == "not_assessable"
    assert result.level in {"low", "medium"}


def test_stability_excludes_negative_velocity_but_direction_is_mixed():
    result = _confidence(
        [
            ("1 June 2025", 20),
            ("2 June 2025", 40),
            ("3 June 2025", 39),
            ("4 June 2025", 60),
        ]
    )

    assert result.direction_consistency == "mixed"
    assert result.negative_interval_count == 1
    assert result.velocity_stability == "stable"
    assert result.level in {"low", "medium"}


def test_zero_velocity_is_included_in_stability_sample():
    result = _confidence(
        [
            ("1 June 2025", 10),
            ("2 June 2025", 20),
            ("3 June 2025", 20),
        ]
    )

    assert result.zero_interval_count == 1
    assert result.velocity_stability == "unstable"


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([1.0, 1.5], "stable"),
        ([1.0, 3.0], "variable"),
        ([1.0, 8.0], "unstable"),
    ],
)
def test_stability_thresholds_are_deterministic(values, expected):
    assert ForecastConfidenceAnalyzer._classify_stability(values) == expected


@pytest.mark.parametrize(
    ("progresses", "expected"),
    [
        ([0.0, 1.0, 1.0 + (5.0 / 3.0)], "stable"),
        ([0.0, 1.0, 8.0], "variable"),
        ([0.0, 1.0, 9.0], "unstable"),
    ],
)
def test_end_to_end_cv_boundaries(progresses, expected):
    history = ActivityHistory(
        project_name="Metro Project",
        activity_name="Foundation",
        snapshots=[
            ActivitySnapshot(
                report_date=f"{index + 1} June 2025",
                submission_order=index + 1,
                progress_percentage=progress,
            )
            for index, progress in enumerate(progresses)
        ],
    )
    forecast = ForecastResult(
        project_name="Metro Project",
        activity_name="Foundation",
        status="available",
        current_progress=progresses[-1],
        observation_count=len(progresses),
        forecast_method="net_observed_progress_velocity",
    )

    result = ForecastConfidenceAnalyzer().analyze_history(history, forecast)

    assert result.velocity_stability == expected


@pytest.mark.parametrize(
    ("progresses", "expected"),
    [
        ([10, 20, 30], "positive"),
        ([10, 10, 10], "non_positive"),
        ([30, 20, 10], "non_positive"),
        ([10, 20, 20], "mixed"),
        ([20, 10, 20], "mixed"),
    ],
)
def test_direction_consistency_is_separate_from_stability(progresses, expected):
    result = _confidence(
        [
            (f"{index + 1} June 2025", progress)
            for index, progress in enumerate(progresses)
        ]
    )

    assert result.direction_consistency == expected


def test_duplicate_reports_and_aliases_do_not_add_evidence():
    tracker = _service(
        [("1 June 2025", 10), ("2 June 2025", 20)],
    )
    tracker.record(
        ProgressReport(
            project_name=" metro project ",
            report_date="2 June 2025",
            activities=[
                ActivityProgress(
                    activity_name=" foundation ",
                    progress_percentage=20,
                )
            ],
        )
    )
    history = tracker.get_activity_history(" METRO PROJECT ", "FOUNDATION")
    forecast = ForecastAnalyzer(tracker).analyze_activity(
        " METRO PROJECT ", "FOUNDATION"
    )

    assert history is not None
    assert forecast is not None
    result = ForecastConfidenceAnalyzer().analyze_history(history, forecast)

    assert result.total_snapshot_count == 2
    assert result.usable_observation_count == 2
    assert result.interval_count == 1


def test_all_missing_and_invalid_progress_is_excluded_from_evidence():
    history = ActivityHistory(
        project_name="Metro Project",
        activity_name="Foundation",
        snapshots=[
            ActivitySnapshot.model_construct(
                report_date="1 June 2025",
                submission_order=1,
                progress_percentage=None,
            ),
            ActivitySnapshot.model_construct(
                report_date="2 June 2025",
                submission_order=2,
                progress_percentage=float("nan"),
            ),
            ActivitySnapshot.model_construct(
                report_date="3 June 2025",
                submission_order=3,
                progress_percentage=True,
            ),
        ],
    )
    forecast = ForecastResult(
        project_name="Metro Project",
        activity_name="Foundation",
        status="insufficient_data",
        observation_count=0,
        forecast_method="net_observed_progress_velocity",
    )

    result = ForecastConfidenceAnalyzer().analyze_history(history, forecast)

    assert result.total_snapshot_count == 3
    assert result.usable_observation_count == 0
    assert result.missing_progress_count == 3
    assert result.assessment_status == "not_assessed"


@pytest.mark.parametrize("status", ["insufficient_data", "unavailable"])
def test_non_available_forecast_is_not_assessed(status):
    entries = [("1 June 2025", 50)]
    if status == "unavailable":
        entries = [("1 June 2025", 50), ("2 June 2025", 40)]

    tracker = _service(entries)
    history = tracker.get_activity_history("Metro Project", "Foundation")
    forecast = ForecastAnalyzer(tracker).analyze_activity(
        "Metro Project", "Foundation"
    )
    assert history is not None
    assert forecast is not None
    assert forecast.status == status
    result = ForecastConfidenceAnalyzer().analyze_history(history, forecast)

    assert result.assessment_status == "not_assessed"
    assert result.level is None


def test_completed_forecast_is_not_applicable():
    tracker = _service([("1 June 2025", 80), ("2 June 2025", 100)])
    history = tracker.get_activity_history("Metro Project", "Foundation")
    forecast = ForecastAnalyzer(tracker).analyze_activity(
        "Metro Project", "Foundation"
    )
    assert history is not None
    assert forecast is not None
    result = ForecastConfidenceAnalyzer().analyze_history(history, forecast)

    assert result.assessment_status == "not_applicable"
    assert result.level is None


def test_missing_or_malformed_dates_use_fallback_and_are_unusable_for_intervals():
    result = _confidence(
        [("1 June 2025", 10), ("not-a-date", 20), ("3 June 2025", 30)]
    )

    assert result.date_quality == "submission_order_fallback"
    assert result.velocity_stability == "not_assessable"
    assert result.direction_consistency == "not_assessable"
    assert result.level is None
    assert result.assessment_status == "not_assessed"


def test_fallback_ordering_excludes_negative_date_gap_and_explains_it():
    tracker = _service(
        [("10 June 2025", 10), ("not-a-date", None), ("1 June 2025", 30)]
    )
    history = tracker.get_activity_history("Metro Project", "Foundation")
    forecast = ForecastResult(
        project_name="Metro Project",
        activity_name="Foundation",
        status="available",
        current_progress=30,
        observation_count=2,
        forecast_method="net_observed_progress_velocity",
    )
    assert history is not None

    result = ForecastConfidenceAnalyzer().analyze_history(history, forecast)

    assert result.interval_count == 1
    assert result.valid_velocity_interval_count == 0
    assert result.zero_day_gap_count == 0
    assert result.date_quality == "submission_order_fallback"
    assert any("negative day gap" in item for item in result.evidence)


@pytest.mark.parametrize(
    ("entries", "expected_level"),
    [
        (
            [("1 June 2025", 10), ("2 June 2025", 20)],
            "low",
        ),
        (
            [("1 June 2025", 10), ("2 June 2025", 20), ("3 June 2025", 30)],
            "medium",
        ),
        (
            [
                ("1 June 2025", 10),
                ("2 June 2025", 20),
                ("3 June 2025", 30),
                ("4 June 2025", 40),
            ],
            "medium",
        ),
        (
            [
                ("1 June 2025", 10),
                ("2 June 2025", 20),
                ("3 June 2025", 30),
                ("4 June 2025", 40),
                ("5 June 2025", 50),
            ],
            "high",
        ),
        (
            [
                ("1 June 2025", 10),
                ("2 June 2025", None),
                ("3 June 2025", 20),
                ("4 June 2025", 30),
                ("5 June 2025", 40),
                ("6 June 2025", 50),
            ],
            "medium",
        ),
        (
            [
                ("1 June 2025", 10),
                ("1 June 2025", 20),
                ("2 June 2025", 30),
                ("3 June 2025", 40),
                ("4 June 2025", 50),
            ],
            {"low", "medium"},
        ),
        (
            [
                ("1 June 2025", 10),
                ("1 June 2025", 20),
                ("1 June 2025", 30),
                ("1 June 2025", 40),
                ("2 June 2025", 50),
            ],
            {"low", "medium"},
        ),
        (
            [
                ("1 June 2025", 0),
                ("2 June 2025", 1),
                ("3 June 2025", 4),
                ("4 June 2025", 5),
                ("5 June 2025", 8),
            ],
            {"low", "medium"},
        ),
        (
            [
                ("1 June 2025", 10),
                ("2 June 2025", 20),
                ("3 June 2025", 19),
                ("4 June 2025", 29),
                ("5 June 2025", 39),
            ],
            {"low", "medium"},
        ),
    ],
)
def test_locked_confidence_decision_table(entries, expected_level):
    result = _confidence(entries)

    assert result.assessment_status == "assessed"
    if isinstance(expected_level, set):
        assert result.level in expected_level
    else:
        assert result.level == expected_level


def test_unstable_stability_is_low():
    result = _confidence(
        [
            ("1 June 2025", 0),
            ("2 June 2025", 1),
            ("3 June 2025", 9),
            ("4 June 2025", 10),
            ("5 June 2025", 18),
        ]
    )

    assert result.velocity_stability == "unstable"
    assert result.level == "low"


def test_non_positive_direction_is_low_when_supplied_available_forecast():
    tracker = _service([("1 June 2025", 30), ("2 June 2025", 20)])
    history = tracker.get_activity_history("Metro Project", "Foundation")
    forecast = ForecastResult(
        project_name="Metro Project",
        activity_name="Foundation",
        status="available",
        current_progress=20,
        observation_count=2,
        forecast_method="net_observed_progress_velocity",
    )
    assert history is not None

    result = ForecastConfidenceAnalyzer().analyze_history(history, forecast)

    assert result.direction_consistency == "non_positive"
    assert result.level == "low"


def test_analysis_service_composition_preserves_phase3_1_forecast_fields():
    from app.services.analysis_service import AnalysisService

    tracker = ProgressTracker()
    for report_date, progress in [
        ("1 June 2025", 35),
        ("15 June 2025", 57),
    ]:
        tracker.record(
            ProgressReport(
                project_name="Metro Project",
                report_date=report_date,
                activities=[
                    ActivityProgress(
                        activity_name="Foundation",
                        progress_percentage=progress,
                    )
                ],
            )
        )

    service = AnalysisService(tracker)
    direct = service.forecast_analyzer.analyze_activity(
        "Metro Project", "Foundation"
    )
    composed = service.analyze_activity_forecast(
        "Metro Project", "Foundation"
    )

    assert direct is not None
    assert composed is not None
    fields = (
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
    )
    assert {field: getattr(composed, field) for field in fields} == {
        field: getattr(direct, field) for field in fields
    }
    assert composed.confidence is not None


def test_openapi_and_evidence_fields_are_supported_by_nested_model():
    result = _confidence(
        [("1 June 2025", 10), ("2 June 2025", 20), ("3 June 2025", 30)]
    )

    assert result.evidence
    assert any("usable progress observations" in item for item in result.evidence)
    assert not hasattr(result, "score")
    assert not hasattr(result, "probability")


def test_delay_and_issue_observations_do_not_change_confidence():
    baseline = _confidence(
        [("1 June 2025", 10), ("2 June 2025", 20), ("3 June 2025", 30)]
    )
    with_evidence = _confidence(
        [("1 June 2025", 10), ("2 June 2025", 20), ("3 June 2025", 30)],
        delay="Rain",
        issues=["Access problem"],
    )

    assert with_evidence == baseline
