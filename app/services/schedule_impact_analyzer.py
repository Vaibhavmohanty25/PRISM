import math
from collections import defaultdict

from app.schemas.project_data import (
    ActivityHistory,
    ActivityScheduleImpact,
    ProjectScheduleImpact,
)
from app.services.progress_tracker import ProgressTracker
from app.services.trend_analyzer import TrendAnalyzer, _ordered_snapshots


def _valid_delay_hours(value: float | None) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _normalized_reason(value: str | None) -> str | None:
    if value is None:
        return None

    reason = value.strip()
    return reason if reason else None


class ScheduleImpactAnalyzer:
    """Deterministic summaries of explicitly reported delay observations."""

    def __init__(self, tracker: ProgressTracker) -> None:
        self.tracker = tracker
        self.trend_analyzer = TrendAnalyzer(tracker)

    def analyze_history(
        self,
        history: ActivityHistory,
    ) -> ActivityScheduleImpact:
        ordered = _ordered_snapshots(history.snapshots)
        delay_snapshots = []
        reason_occurrences: dict[str, set[int]] = defaultdict(set)
        display_reasons: dict[str, str] = {}

        for snapshot_index, snapshot in enumerate(ordered):
            reason = _normalized_reason(snapshot.delay_reason)
            has_duration = _valid_delay_hours(
                snapshot.delay_duration_hours
            )

            if not has_duration and reason is None:
                continue

            delay_snapshots.append(snapshot)

            if reason is not None:
                normalized = reason.casefold()
                reason_occurrences[normalized].add(snapshot_index)
                display_reasons.setdefault(normalized, reason)

        repeated_reasons = [
            display_reasons[normalized]
            for normalized in reason_occurrences
            if len(reason_occurrences[normalized]) >= 2
        ]

        latest = delay_snapshots[-1] if delay_snapshots else None
        latest_reason = (
            _normalized_reason(latest.delay_reason)
            if latest is not None
            else None
        )
        latest_hours = (
            latest.delay_duration_hours
            if latest is not None
            and _valid_delay_hours(latest.delay_duration_hours)
            else None
        )
        trend = self.trend_analyzer.analyze_history(history)

        if not delay_snapshots:
            status = "insufficient_data"
            summary = (
                "No valid delay duration or delay reason was reported."
            )
        else:
            status = "available"
            summary = (
                "Observed delay information was reported in "
                f"{len(delay_snapshots)} snapshot(s)."
            )

        return ActivityScheduleImpact(
            project_name=history.project_name,
            activity_name=history.activity_name,
            status=status,
            delay_observation_count=len(delay_snapshots),
            repeated_delay_reasons=repeated_reasons,
            latest_delay_hours=latest_hours,
            latest_delay_reason=latest_reason,
            progress_trend=trend.trend,
            summary=summary,
        )

    def analyze_activity(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityScheduleImpact | None:
        history = self.tracker.get_activity_history(
            project_name,
            activity_name,
        )

        if history is None:
            return None

        return self.analyze_history(history)

    def analyze_project(
        self,
        project_name: str | None,
    ) -> ProjectScheduleImpact | None:
        if project_name not in self.tracker.get_projects():
            return None

        histories = self.tracker.get_all_histories(project_name)
        return ProjectScheduleImpact(
            project_name=project_name or "",
            activities=[
                self.analyze_history(history)
                for history in histories
            ],
        )
