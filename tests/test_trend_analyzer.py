from app.schemas.project_data import (
    ActivityHistory,
    ActivityProgress,
    ActivitySnapshot,
    ProgressReport,
)
from app.services.progress_tracker import ProgressTracker
from app.services.trend_analyzer import (
    TrendAnalyzer,
    parse_report_date,
)


def _make_report(
    *,
    project_name: str,
    report_date: str | None,
    activity_name: str,
    progress: float | None,
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


def _record_reports(
    tracker: ProgressTracker,
    project_name: str,
    activity_name: str,
    entries: list[tuple[str | None, float | None]],
) -> TrendAnalyzer:
    for report_date, progress in entries:
        tracker.record(
            _make_report(
                project_name=project_name,
                report_date=report_date,
                activity_name=activity_name,
                progress=progress,
            )
        )

    return TrendAnalyzer(tracker)


def test_improving_trend():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Delhi Metro Extension",
        "Foundation RCC work",
        [
            ("1 June 2025", 35),
            ("8 June 2025", 48),
            ("15 June 2025", 57),
        ],
    )

    result = analyzer.analyze_activity(
        "Delhi Metro Extension",
        "Foundation RCC work",
    )

    assert result.trend == "improving"
    assert result.progress_deltas == [13.0, 9.0]
    assert result.average_progress_delta == 11.0
    assert result.first_progress == 35
    assert result.last_progress == 57


def test_stalled_trend():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Metro Project",
        "Foundation RCC work",
        [
            ("1 June 2025", 50),
            ("8 June 2025", 50.5),
            ("15 June 2025", 50.0),
        ],
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.trend == "stalled"
    assert result.progress_deltas == [0.5, -0.5]
    assert result.average_progress_delta == 0.0


def test_declining_trend():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Metro Project",
        "Foundation RCC work",
        [
            ("1 June 2025", 60),
            ("8 June 2025", 50),
            ("15 June 2025", 40),
        ],
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.trend == "declining"
    assert result.progress_deltas == [-10.0, -10.0]
    assert result.average_progress_delta == -10.0


def test_insufficient_data_for_single_snapshot():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Metro Project",
        "Foundation RCC work",
        [("5 June 2025", 70)],
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.trend == "insufficient_data"
    assert result.progress_deltas == []
    assert result.average_progress_delta is None
    assert result.average_velocity_per_day is None
    assert result.snapshot_count == 1


def test_missing_progress_values_are_handled_safely():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Highway Expansion Project",
        "Earthwork excavation",
        [
            ("1 June 2025", None),
            ("8 June 2025", 20),
            ("15 June 2025", 35),
        ],
    )

    result = analyzer.analyze_activity(
        "Highway Expansion Project",
        "Earthwork excavation",
    )

    assert result.trend == "improving"
    assert result.progress_deltas == [15.0]
    assert result.first_progress == 20
    assert result.last_progress == 35


def test_insufficient_data_when_no_progress_values():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Highway Expansion Project",
        "Earthwork excavation",
        [
            ("1 June 2025", None),
            ("8 June 2025", None),
        ],
    )

    result = analyzer.analyze_activity(
        "Highway Expansion Project",
        "Earthwork excavation",
    )

    assert result.trend == "insufficient_data"
    assert result.progress_deltas == []
    assert result.first_progress is None
    assert result.last_progress is None


def test_known_date_gap_velocity_calculation():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Delhi Metro Extension",
        "Foundation RCC work",
        [
            ("5 June 2025", 35),
            ("12 June 2025", 49),
        ],
    )

    result = analyzer.analyze_activity(
        "Delhi Metro Extension",
        "Foundation RCC work",
    )

    assert result.average_velocity_per_day == 2.0


def test_unparseable_dates_use_submission_order_without_velocity():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Metro Project",
        "Foundation RCC work",
        [
            (None, 30),
            (None, 45),
        ],
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.trend == "improving"
    assert result.progress_deltas == [15.0]
    assert result.average_velocity_per_day is None


def test_mixed_parseable_dates_use_submission_order_without_velocity():
    tracker = ProgressTracker()
    analyzer = _record_reports(
        tracker,
        "Metro Project",
        "Foundation RCC work",
        [
            (None, 10),
            ("8 June 2025", 30),
            ("15 June 2025", 50),
        ],
    )

    result = analyzer.analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.progress_deltas == [20.0, 20.0]
    assert result.average_velocity_per_day is None


def test_analyze_project_returns_all_activity_trends():
    tracker = ProgressTracker()

    tracker.record(
        ProgressReport(
            project_name="Metro Project",
            report_date="1 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Foundation RCC work",
                    progress_percentage=30,
                ),
                ActivityProgress(
                    activity_name="Brick masonry work",
                    progress_percentage=10,
                ),
            ],
        )
    )
    tracker.record(
        ProgressReport(
            project_name="Metro Project",
            report_date="8 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Foundation RCC work",
                    progress_percentage=45,
                ),
                ActivityProgress(
                    activity_name="Brick masonry work",
                    progress_percentage=10.5,
                ),
            ],
        )
    )

    analyzer = TrendAnalyzer(tracker)
    results = analyzer.analyze_project("Metro Project")

    assert len(results) == 2

    trends = {
        result.activity_name: result.trend
        for result in results
    }

    assert trends["Foundation RCC work"] == "improving"
    assert trends["Brick masonry work"] == "stalled"


def test_parse_report_date_supports_existing_format():
    assert parse_report_date("5 June 2025").isoformat() == (
        "2025-06-05"
    )


def test_analyze_history_sorts_by_date_not_submission_order():
    history = ActivityHistory(
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        snapshots=[
            ActivitySnapshot(
                report_date="15 June 2025",
                submission_order=2,
                progress_percentage=57,
            ),
            ActivitySnapshot(
                report_date="1 June 2025",
                submission_order=1,
                progress_percentage=35,
            ),
        ],
    )

    analyzer = TrendAnalyzer(ProgressTracker())
    result = analyzer.analyze_history(history)

    assert result.progress_deltas == [22.0]
    assert result.trend == "improving"
