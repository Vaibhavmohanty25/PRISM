from collections import defaultdict

from app.schemas.project_data import (
    ActivityHistory,
    RiskLevel,
    RiskResult,
    TrendResult,
)
from app.services.progress_tracker import ProgressTracker
from app.services.trend_analyzer import TrendAnalyzer

LOW_VELOCITY_THRESHOLD = 0.5

TREND_SCORES = {
    "improving": 0,
    "stalled": 30,
    "declining": 60,
}


def _normalize_signal(value: str) -> str:
    return value.strip().lower()


def _repeated_values(
    history: ActivityHistory,
    values_for_snapshot: list[list[str]],
) -> list[str]:
    occurrences: dict[str, set[int]] = defaultdict(set)
    display_values: dict[str, str] = {}

    for snapshot_index, values in enumerate(values_for_snapshot):
        for value in values:
            normalized = _normalize_signal(value)
            if not normalized:
                continue

            occurrences[normalized].add(snapshot_index)
            display_values.setdefault(normalized, value.strip())

    return [
        display_values[normalized]
        for normalized in occurrences
        if len(occurrences[normalized]) >= 2
    ]


class RiskAnalyzer:
    """
    Deterministic observed-risk analysis over tracked activity history.

    Scores represent explainable historical signals, not probabilities.
    This layer does not predict completion dates or use an LLM.
    """

    def __init__(self, tracker: ProgressTracker) -> None:
        self.tracker = tracker
        self.trend_analyzer = TrendAnalyzer(tracker)

    def _repeated_delays(
        self,
        history: ActivityHistory,
    ) -> list[str]:
        return _repeated_values(
            history,
            [
                [snapshot.delay_reason]
                if snapshot.delay_reason is not None
                else []
                for snapshot in history.snapshots
            ],
        )

    def _repeated_issues(
        self,
        history: ActivityHistory,
    ) -> list[str]:
        return _repeated_values(
            history,
            [snapshot.issues for snapshot in history.snapshots],
        )

    def analyze_history(
        self,
        history: ActivityHistory,
    ) -> RiskResult:
        trend_result: TrendResult = self.trend_analyzer.analyze_history(
            history
        )

        repeated_delays = self._repeated_delays(history)
        repeated_issues = self._repeated_issues(history)

        if trend_result.trend == "insufficient_data":
            return RiskResult(
                project_name=history.project_name,
                activity_name=history.activity_name,
                risk_level="insufficient_data",
                risk_score=0,
                risk_signals=[],
                repeated_delays=repeated_delays,
                repeated_issues=repeated_issues,
                trend=trend_result.trend,
                average_velocity_per_day=(
                    trend_result.average_velocity_per_day
                ),
                progress_deltas=list(trend_result.progress_deltas),
                snapshot_count=trend_result.snapshot_count,
            )

        risk_score = TREND_SCORES[trend_result.trend]
        risk_signals: list[str] = []

        if trend_result.trend == "stalled":
            risk_signals.append("Progress has stalled")
        elif trend_result.trend == "declining":
            risk_signals.append("Progress is declining")

        if (
            trend_result.average_velocity_per_day is not None
            and trend_result.average_velocity_per_day
            < LOW_VELOCITY_THRESHOLD
        ):
            risk_score += 20
            risk_signals.append("Progress velocity is very low")

        for delay in repeated_delays:
            risk_score += 15
            risk_signals.append(f"Repeated delay: {delay}")

        for issue in repeated_issues:
            risk_score += 10
            risk_signals.append(f"Repeated issue: {issue}")

        risk_score = min(risk_score, 100)
        risk_level = self._classify_score(risk_score)

        if trend_result.trend == "stalled":
            risk_level = self._at_least_medium(risk_level)
        elif trend_result.trend == "declining":
            risk_level = "high"

        return RiskResult(
            project_name=history.project_name,
            activity_name=history.activity_name,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_signals=risk_signals,
            repeated_delays=repeated_delays,
            repeated_issues=repeated_issues,
            trend=trend_result.trend,
            average_velocity_per_day=(
                trend_result.average_velocity_per_day
            ),
            progress_deltas=list(trend_result.progress_deltas),
            snapshot_count=trend_result.snapshot_count,
        )

    @staticmethod
    def _classify_score(score: int) -> RiskLevel:
        if score <= 24:
            return "low"
        if score <= 59:
            return "medium"
        return "high"

    @staticmethod
    def _at_least_medium(level: RiskLevel) -> RiskLevel:
        return "high" if level == "high" else "medium"

    def analyze_activity(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> RiskResult | None:
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
    ) -> list[RiskResult]:
        histories = self.tracker.get_all_histories(project_name)
        return [self.analyze_history(history) for history in histories]
