from datetime import datetime, time, timedelta
import math

from app.schemas.project_data import (
    ActivityHistory,
    ForecastResult,
)
from app.services.progress_tracker import ProgressTracker
from app.services.trend_analyzer import (
    _average_velocity_per_day,
    _ordered_snapshots,
    parse_report_date,
)


FORECAST_METHOD = "net_observed_progress_velocity"


def _usable_progress(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0 <= value <= 100
    )


class ForecastAnalyzer:
    """Deterministic activity forecasts from observed progress history."""

    def __init__(self, tracker: ProgressTracker) -> None:
        self.tracker = tracker

    @staticmethod
    def _result(
        history: ActivityHistory,
        *,
        status: str,
        current_progress: float | None,
        remaining_progress: float | None,
        historical_velocity: float | None,
        observation_count: int,
        first_report_date: str | None,
        latest_report_date: str | None,
        evidence: list[str] | None = None,
        data_note: str | None = None,
        estimated_days: float | None = None,
        estimated_date: str | None = None,
    ) -> ForecastResult:
        return ForecastResult(
            project_name=history.project_name,
            activity_name=history.activity_name,
            status=status,
            current_progress=current_progress,
            remaining_progress=remaining_progress,
            historical_velocity_per_day=historical_velocity,
            estimated_days_to_completion=estimated_days,
            estimated_completion_date=estimated_date,
            observation_count=observation_count,
            first_report_date=first_report_date,
            latest_report_date=latest_report_date,
            forecast_method=FORECAST_METHOD,
            evidence=evidence or [],
            data_note=data_note,
        )

    def analyze_history(self, history: ActivityHistory) -> ForecastResult:
        ordered = _ordered_snapshots(history.snapshots)
        usable = [
            snapshot
            for snapshot in ordered
            if _usable_progress(snapshot.progress_percentage)
        ]

        first = usable[0] if usable else None
        latest = usable[-1] if usable else None
        current_progress = (
            float(latest.progress_percentage)
            if latest is not None
            else None
        )
        remaining_progress = (
            100.0 - current_progress
            if current_progress is not None
            else None
        )
        first_report_date = first.report_date if first is not None else None
        latest_report_date = latest.report_date if latest is not None else None

        if len(usable) < 2:
            return self._result(
                history,
                status="insufficient_data",
                current_progress=current_progress,
                remaining_progress=remaining_progress,
                historical_velocity=None,
                observation_count=len(usable),
                first_report_date=first_report_date,
                latest_report_date=latest_report_date,
                data_note=(
                    "At least two usable progress observations are required "
                    "to calculate a forecast."
                ),
            )

        historical_velocity = _average_velocity_per_day(ordered)

        if historical_velocity is None or not math.isfinite(historical_velocity):
            return self._result(
                history,
                status="unavailable",
                current_progress=current_progress,
                remaining_progress=remaining_progress,
                historical_velocity=historical_velocity,
                observation_count=len(usable),
                first_report_date=first_report_date,
                latest_report_date=latest_report_date,
                data_note=(
                    "Usable report dates are required to calculate "
                    "historical velocity and completion date."
                ),
            )

        if historical_velocity <= 0:
            return self._result(
                history,
                status="unavailable",
                current_progress=current_progress,
                remaining_progress=remaining_progress,
                historical_velocity=historical_velocity,
                observation_count=len(usable),
                first_report_date=first_report_date,
                latest_report_date=latest_report_date,
                data_note=(
                    "Historical net progress velocity must be positive "
                    "for an estimated completion timeframe."
                ),
            )

        latest_date = parse_report_date(latest_report_date)
        if latest_date is None:
            return self._result(
                history,
                status="unavailable",
                current_progress=current_progress,
                remaining_progress=remaining_progress,
                historical_velocity=historical_velocity,
                observation_count=len(usable),
                first_report_date=first_report_date,
                latest_report_date=latest_report_date,
                data_note=(
                    "A usable latest report date is required to calculate "
                    "an estimated completion date."
                ),
            )

        estimated_days = remaining_progress / historical_velocity
        completion_datetime = datetime.combine(
            latest_date,
            time.min,
        ) + timedelta(days=estimated_days)
        estimated_date = completion_datetime.date().isoformat()
        evidence = [
            f"Latest observed progress: {current_progress:g}%.",
            (
                "Historical net progress velocity: "
                f"{historical_velocity:g} percentage points/day."
            ),
            f"Remaining progress: {remaining_progress:g} percentage points.",
            f"Estimated completion duration: {estimated_days:g} days.",
            f"Progress observation count: {len(usable)}.",
        ]

        return self._result(
            history,
            status="available",
            current_progress=current_progress,
            remaining_progress=remaining_progress,
            historical_velocity=historical_velocity,
            estimated_days=estimated_days,
            estimated_date=estimated_date,
            observation_count=len(usable),
            first_report_date=first_report_date,
            latest_report_date=latest_report_date,
            evidence=evidence,
        )

    def analyze_activity(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ForecastResult | None:
        history = self.tracker.get_activity_history(
            project_name,
            activity_name,
        )

        if history is None:
            return None

        return self.analyze_history(history)
