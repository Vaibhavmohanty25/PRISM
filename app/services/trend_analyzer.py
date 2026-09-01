from datetime import date, datetime

from app.schemas.project_data import (
    ActivityHistory,
    ActivitySnapshot,
    TrendClassification,
    TrendResult,
)
from app.services.progress_tracker import ProgressTracker

STALL_THRESHOLD = 1.0

DATE_FORMATS = (
    "%d %B %Y",
    "%d %b %Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
)


def parse_report_date(
    report_date: str | None,
) -> date | None:
    if not report_date:
        return None

    value = report_date.strip()

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(
                value,
                date_format,
            ).date()
        except ValueError:
            continue

    return None


def _ordered_snapshots(
    snapshots: list[ActivitySnapshot],
) -> list[ActivitySnapshot]:
    parsed_dates = [
        parse_report_date(snapshot.report_date)
        for snapshot in snapshots
    ]

    # A partially dated history cannot be reliably ordered by date. In
    # that case, preserve ingestion order for both deltas and velocity.
    if any(parsed_date is None for parsed_date in parsed_dates):
        return sorted(
            snapshots,
            key=lambda snapshot: snapshot.submission_order,
        )

    return sorted(
        snapshots,
        key=lambda snapshot: (
            parse_report_date(snapshot.report_date),
            snapshot.submission_order,
        ),
    )


def _consecutive_progress_deltas(
    snapshots: list[ActivitySnapshot],
) -> list[float]:
    deltas: list[float] = []

    previous_progress: float | None = None

    for snapshot in snapshots:
        current_progress = snapshot.progress_percentage

        if current_progress is None:
            continue

        if previous_progress is not None:
            deltas.append(
                current_progress - previous_progress
            )

        previous_progress = current_progress

    return deltas


def _classify_trend(
    deltas: list[float],
) -> TrendClassification:
    if not deltas:
        return "insufficient_data"

    average_delta = sum(deltas) / len(deltas)

    if average_delta > STALL_THRESHOLD:
        return "improving"

    if average_delta < -STALL_THRESHOLD:
        return "declining"

    return "stalled"


def _progress_values(
    snapshots: list[ActivitySnapshot],
) -> list[float]:
    return [
        snapshot.progress_percentage
        for snapshot in snapshots
        if snapshot.progress_percentage is not None
    ]


def _average_velocity_per_day(
    snapshots: list[ActivitySnapshot],
) -> float | None:
    if any(
        parse_report_date(snapshot.report_date) is None
        for snapshot in snapshots
    ):
        return None

    dated_snapshots = []

    for snapshot in snapshots:
        parsed_date = parse_report_date(
            snapshot.report_date
        )

        if (
            parsed_date is None
            or snapshot.progress_percentage is None
        ):
            continue

        dated_snapshots.append(
            (parsed_date, snapshot.progress_percentage)
        )

    if len(dated_snapshots) < 2:
        return None

    first_date, first_progress = dated_snapshots[0]
    last_date, last_progress = dated_snapshots[-1]

    day_gap = (last_date - first_date).days

    if day_gap <= 0:
        return None

    return (last_progress - first_progress) / day_gap


class TrendAnalyzer:
    """
    Deterministic trend analysis over ProgressTracker history.
    """

    def __init__(
        self,
        tracker: ProgressTracker,
    ) -> None:
        self.tracker = tracker

    def analyze_history(
        self,
        history: ActivityHistory,
    ) -> TrendResult:
        ordered = _ordered_snapshots(
            history.snapshots
        )

        if len(ordered) < 2:
            progress_values = _progress_values(ordered)

            return TrendResult(
                project_name=history.project_name,
                activity_name=history.activity_name,
                trend="insufficient_data",
                snapshot_count=len(ordered),
                progress_deltas=[],
                average_progress_delta=None,
                average_velocity_per_day=None,
                first_progress=(
                    progress_values[0]
                    if progress_values
                    else None
                ),
                last_progress=(
                    progress_values[-1]
                    if progress_values
                    else None
                ),
            )

        deltas = _consecutive_progress_deltas(
            ordered
        )
        progress_values = _progress_values(ordered)

        return TrendResult(
            project_name=history.project_name,
            activity_name=history.activity_name,
            trend=_classify_trend(deltas),
            snapshot_count=len(ordered),
            progress_deltas=deltas,
            average_progress_delta=(
                sum(deltas) / len(deltas)
                if deltas
                else None
            ),
            average_velocity_per_day=(
                _average_velocity_per_day(ordered)
            ),
            first_progress=(
                progress_values[0]
                if progress_values
                else None
            ),
            last_progress=(
                progress_values[-1]
                if progress_values
                else None
            ),
        )

    def analyze_project(
        self,
        project_name: str | None,
    ) -> list[TrendResult]:
        histories = self.tracker.get_all_histories(
            project_name
        )

        return [
            self.analyze_history(history)
            for history in histories
        ]

    def analyze_activity(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> TrendResult | None:
        history = self.tracker.get_activity_history(
            project_name,
            activity_name,
        )

        if history is None:
            return None

        return self.analyze_history(history)
