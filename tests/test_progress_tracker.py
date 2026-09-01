from app.schemas.project_data import (
    ActivityProgress,
    ProgressReport,
)
from app.services.progress_tracker import (
    ProgressTracker,
    UNASSIGNED_PROJECT,
)


def _make_report(
    *,
    project_name: str | None,
    report_date: str | None,
    activities: list[ActivityProgress],
) -> ProgressReport:
    return ProgressReport(
        project_name=project_name,
        report_date=report_date,
        activities=activities,
    )


def _activity(
    name: str,
    progress: float | None = None,
    quantity: float | None = None,
) -> ActivityProgress:
    return ActivityProgress(
        activity_name=name,
        progress_percentage=progress,
        quantity_completed=quantity,
        unit="cubic meters" if quantity is not None else None,
        status="In Progress" if progress is not None else None,
        issues=["Rain"] if progress == 70 else [],
        delay_reason="Rain" if progress == 70 else None,
        delay_duration_hours=3 if progress == 70 else None,
    )


def test_record_multiple_reports_for_one_project():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Delhi Metro Extension",
            report_date="1 June 2025",
            activities=[_activity("Foundation RCC work", 35)],
        )
    )
    tracker.record(
        _make_report(
            project_name="Delhi Metro Extension",
            report_date="8 June 2025",
            activities=[_activity("Foundation RCC work", 48)],
        )
    )

    history = tracker.get_activity_history(
        "Delhi Metro Extension",
        "Foundation RCC work",
    )

    assert history is not None
    assert history.project_name == "Delhi Metro Extension"
    assert len(history.snapshots) == 2
    assert history.snapshots[0].progress_percentage == 35
    assert history.snapshots[1].progress_percentage == 48


def test_activity_history_accumulates_fields():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Metro Project",
            report_date="5 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Foundation RCC work",
                    quantity_completed=120,
                    unit="cubic meters",
                    progress_percentage=70,
                    status="In Progress",
                    issues=["Heavy rainfall"],
                    delay_reason="Heavy rainfall",
                    delay_duration_hours=3,
                )
            ],
        )
    )

    snapshot = tracker.get_activity_history(
        "Metro Project",
        "Foundation RCC work",
    ).snapshots[0]

    assert snapshot.report_date == "5 June 2025"
    assert snapshot.progress_percentage == 70
    assert snapshot.quantity_completed == 120
    assert snapshot.unit == "cubic meters"
    assert snapshot.status == "In Progress"
    assert snapshot.issues == ["Heavy rainfall"]
    assert snapshot.delay_reason == "Heavy rainfall"
    assert snapshot.delay_duration_hours == 3


def test_activity_name_normalization():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Metro Project",
            report_date="1 June 2025",
            activities=[_activity("  Foundation RCC work ", 30)],
        )
    )
    tracker.record(
        _make_report(
            project_name="Metro Project",
            report_date="8 June 2025",
            activities=[_activity("foundation rcc work", 45)],
        )
    )

    history = tracker.get_activity_history(
        "Metro Project",
        "FOUNDATION RCC WORK",
    )

    assert history is not None
    assert len(history.snapshots) == 2
    assert history.activity_name == "  Foundation RCC work ".strip()


def test_missing_progress_values_are_stored():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Highway Expansion Project",
            report_date="7 June 2025",
            activities=[
                ActivityProgress(
                    activity_name="Earthwork excavation",
                    quantity_completed=350,
                    unit="cubic meters",
                    progress_percentage=None,
                    status="In Progress",
                )
            ],
        )
    )

    snapshot = tracker.get_activity_history(
        "Highway Expansion Project",
        "Earthwork excavation",
    ).snapshots[0]

    assert snapshot.progress_percentage is None
    assert snapshot.quantity_completed == 350
    assert snapshot.status == "In Progress"


def test_missing_report_dates_use_submission_order():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Metro Project",
            report_date=None,
            activities=[_activity("Foundation RCC work", 20)],
        )
    )
    tracker.record(
        _make_report(
            project_name="Metro Project",
            report_date=None,
            activities=[_activity("Foundation RCC work", 35)],
        )
    )

    history = tracker.get_activity_history(
        "Metro Project",
        "Foundation RCC work",
    )

    assert history.snapshots[0].submission_order == 1
    assert history.snapshots[1].submission_order == 2
    assert history.snapshots[0].report_date is None


def test_new_activity_appearing_in_later_report():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Metro Project",
            report_date="1 June 2025",
            activities=[_activity("Foundation RCC work", 30)],
        )
    )
    tracker.record(
        _make_report(
            project_name="Metro Project",
            report_date="8 June 2025",
            activities=[
                _activity("Foundation RCC work", 45),
                _activity("Brick masonry work", 10),
            ],
        )
    )

    histories = tracker.get_all_histories("Metro Project")

    assert len(histories) == 2

    foundation = tracker.get_activity_history(
        "Metro Project",
        "Foundation RCC work",
    )
    masonry = tracker.get_activity_history(
        "Metro Project",
        "Brick masonry work",
    )

    assert len(foundation.snapshots) == 2
    assert len(masonry.snapshots) == 1
    assert masonry.snapshots[0].progress_percentage == 10


def test_project_isolation():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Project A",
            report_date="1 June 2025",
            activities=[_activity("Foundation RCC work", 30)],
        )
    )
    tracker.record(
        _make_report(
            project_name="Project B",
            report_date="1 June 2025",
            activities=[_activity("Foundation RCC work", 55)],
        )
    )

    history_a = tracker.get_activity_history(
        "Project A",
        "Foundation RCC work",
    )
    history_b = tracker.get_activity_history(
        "Project B",
        "Foundation RCC work",
    )

    assert history_a.snapshots[0].progress_percentage == 30
    assert history_b.snapshots[0].progress_percentage == 55
    assert tracker.get_activity_history(
        "Project A",
        "Brick masonry work",
    ) is None


def test_unassigned_project_bucket():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name=None,
            report_date="1 June 2025",
            activities=[_activity("Foundation RCC work", 25)],
        )
    )

    history = tracker.get_activity_history(
        None,
        "Foundation RCC work",
    )

    assert history.project_name == UNASSIGNED_PROJECT


def test_get_projects_lists_recorded_projects():
    tracker = ProgressTracker()

    tracker.record(
        _make_report(
            project_name="Project B",
            report_date="1 June 2025",
            activities=[_activity("Foundation RCC work", 20)],
        )
    )
    tracker.record(
        _make_report(
            project_name="Project A",
            report_date="1 June 2025",
            activities=[_activity("Foundation RCC work", 20)],
        )
    )

    assert tracker.get_projects() == [
        "Project A",
        "Project B",
    ]
