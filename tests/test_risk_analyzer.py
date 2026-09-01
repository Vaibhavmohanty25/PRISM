from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.progress_tracker import ProgressTracker
from app.services.risk_analyzer import RiskAnalyzer


def _record_reports(
    tracker: ProgressTracker,
    *,
    project_name: str,
    activity_name: str,
    entries: list[tuple[str | None, float | None, str | None, list[str]]],
) -> None:
    for report_date, progress, delay_reason, issues in entries:
        tracker.record(
            ProgressReport(
                project_name=project_name,
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


def test_insufficient_data():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[("5 June 2025", 70, None, [])],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.risk_level == "insufficient_data"
    assert result.trend == "insufficient_data"
    assert result.risk_score == 0


def test_improving_activity_is_low_risk():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("1 June 2025", 35, None, []),
            ("8 June 2025", 48, None, []),
            ("15 June 2025", 57, None, []),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.trend == "improving"
    assert result.risk_level == "low"
    assert result.risk_score == 0


def test_stalled_activity_is_medium_risk():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("1 June 2025", 50, None, []),
            ("8 June 2025", 50.5, None, []),
            ("15 June 2025", 50, None, []),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.trend == "stalled"
    assert result.risk_level == "medium"
    assert "Progress has stalled" in result.risk_signals


def test_declining_activity_is_high_risk():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("1 June 2025", 60, None, []),
            ("8 June 2025", 50, None, []),
            ("15 June 2025", 40, None, []),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.trend == "declining"
    assert result.risk_level == "high"
    assert "Progress is declining" in result.risk_signals


def test_low_velocity_creates_risk_signal():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 35, None, []),
            ("12 June 2025", 37, None, []),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.average_velocity_per_day == 2 / 7
    assert "Progress velocity is very low" in result.risk_signals


def test_repeated_delay_detected():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 35, "Heavy rainfall", []),
            ("12 June 2025", 40, "Heavy rainfall", []),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.repeated_delays == ["Heavy rainfall"]
    assert "Repeated delay: Heavy rainfall" in result.risk_signals


def test_repeated_issue_detected():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 35, None, ["Material shortage"]),
            ("12 June 2025", 40, None, ["Material shortage"]),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.repeated_issues == ["Material shortage"]
    assert "Repeated issue: Material shortage" in result.risk_signals


def test_case_insensitive_delay_normalization():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 35, "Heavy Rainfall", []),
            ("12 June 2025", 40, " heavy rainfall ", []),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.repeated_delays == ["Heavy Rainfall"]


def test_multiple_risk_signals_increase_score():
    simple_tracker = ProgressTracker()
    _record_reports(
        simple_tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 50, None, []),
            ("12 June 2025", 50.5, None, []),
        ],
    )

    signal_tracker = ProgressTracker()
    _record_reports(
        signal_tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 50, "Heavy rainfall", ["Material shortage"]),
            ("12 June 2025", 50.5, "heavy rainfall", ["material shortage"]),
        ],
    )

    simple = RiskAnalyzer(simple_tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )
    combined = RiskAnalyzer(signal_tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert combined.risk_score > simple.risk_score
    assert combined.risk_score == 75


def test_project_analysis_returns_all_activities():
    tracker = ProgressTracker()
    for activity_name in ("Brick masonry work", "Foundation RCC work"):
        _record_reports(
            tracker,
            project_name="Metro Project",
            activity_name=activity_name,
            entries=[
                ("1 June 2025", 30, None, []),
                ("8 June 2025", 45, None, []),
            ],
        )

    results = RiskAnalyzer(tracker).analyze_project("Metro Project")

    assert [result.activity_name for result in results] == [
        "Brick masonry work",
        "Foundation RCC work",
    ]


def test_project_isolation():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Project A",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 50, None, []),
            ("12 June 2025", 50, None, []),
        ],
    )
    _record_reports(
        tracker,
        project_name="Project B",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 50, "Heavy rainfall", ["Material shortage"]),
            ("12 June 2025", 50, "Heavy rainfall", ["Material shortage"]),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Project A",
        "Foundation RCC work",
    )

    assert result.repeated_delays == []
    assert result.repeated_issues == []
    assert result.risk_score == 50


def test_no_false_repeated_delay():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 35, "Heavy rainfall", []),
            ("12 June 2025", 40, "Equipment failure", []),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.repeated_delays == []


def test_no_false_repeated_issue():
    tracker = ProgressTracker()
    _record_reports(
        tracker,
        project_name="Metro Project",
        activity_name="Foundation RCC work",
        entries=[
            ("5 June 2025", 35, None, ["Material shortage"]),
            ("12 June 2025", 40, None, ["Equipment failure"]),
        ],
    )

    result = RiskAnalyzer(tracker).analyze_activity(
        "Metro Project",
        "Foundation RCC work",
    )

    assert result.repeated_issues == []
