from __future__ import annotations

import math
from statistics import mean, pstdev

from app.schemas.project_data import (
    ActivityHistory,
    ForecastConfidence,
    ForecastResult,
)
from app.services.forecast_analyzer import _usable_progress
from app.services.trend_analyzer import _ordered_snapshots, parse_report_date


class ForecastConfidenceAnalyzer:
    """Assess the deterministic quality of evidence behind a forecast."""

    def analyze_history(
        self,
        history: ActivityHistory,
        forecast: ForecastResult,
    ) -> ForecastConfidence:
        ordered = _ordered_snapshots(history.snapshots)
        usable = [
            snapshot
            for snapshot in ordered
            if _usable_progress(snapshot.progress_percentage)
        ]
        missing_progress_count = len(ordered) - len(usable)

        interval_count = max(0, len(usable) - 1)
        valid_velocity_interval_count = 0
        zero_day_gap_count = 0
        positive_interval_count = 0
        zero_interval_count = 0
        negative_interval_count = 0
        negative_day_gap_count = 0
        stability_velocities: list[float] = []

        for previous, current in zip(usable, usable[1:]):
            previous_date = parse_report_date(previous.report_date)
            current_date = parse_report_date(current.report_date)

            if previous_date is None or current_date is None:
                continue

            day_gap = (current_date - previous_date).days
            if day_gap == 0:
                zero_day_gap_count += 1
                continue
            if day_gap < 0:
                negative_day_gap_count += 1
                continue

            velocity = (
                float(current.progress_percentage)
                - float(previous.progress_percentage)
            ) / day_gap
            if not math.isfinite(velocity):
                continue

            valid_velocity_interval_count += 1
            if velocity > 0:
                positive_interval_count += 1
                stability_velocities.append(velocity)
            elif velocity == 0:
                zero_interval_count += 1
                stability_velocities.append(velocity)
            else:
                negative_interval_count += 1

        if valid_velocity_interval_count == 0:
            velocity_stability = "not_assessable"
            direction_consistency = "not_assessable"
        else:
            if positive_interval_count == valid_velocity_interval_count:
                direction_consistency = "positive"
            elif positive_interval_count == 0:
                direction_consistency = "non_positive"
            else:
                direction_consistency = "mixed"
            velocity_stability = self._classify_stability(stability_velocities)

        all_dates_valid = all(
            parse_report_date(snapshot.report_date) is not None
            for snapshot in ordered
        )
        if not all_dates_valid:
            date_quality = "submission_order_fallback"
        elif valid_velocity_interval_count == 0:
            date_quality = "unusable"
        else:
            date_quality = "complete"

        assessment_status, level = self._assess_level(
            forecast,
            usable_count=len(usable),
            missing_progress_count=missing_progress_count,
            velocity_stability=velocity_stability,
            direction_consistency=direction_consistency,
            zero_day_gap_count=zero_day_gap_count,
            stability_velocity_count=len(stability_velocities),
        )

        evidence = [
            f"Forecast evidence includes {len(usable)} usable progress observations.",
            f"{interval_count} historical progress intervals were evaluated.",
            (
                f"{positive_interval_count} of {valid_velocity_interval_count} "
                "valid dated intervals showed positive progress."
            ),
        ]
        if zero_interval_count:
            evidence.append(
                f"{zero_interval_count} valid dated interval showed no progress change."
            )
        if negative_interval_count:
            evidence.append(
                f"{negative_interval_count} valid dated interval showed regressing progress."
            )
        if zero_day_gap_count:
            evidence.append(
                f"{zero_day_gap_count} same-day interval was excluded from velocity evidence."
            )
        if negative_day_gap_count:
            evidence.append(
                f"{negative_day_gap_count} interval with a negative day gap was excluded from velocity evidence."
            )
        if missing_progress_count:
            evidence.append(
                f"{missing_progress_count} snapshot lacked usable progress and was excluded."
            )
        if velocity_stability == "stable":
            evidence.append(
                "Observed interval velocities were stable under the evidence-quality rule."
            )
        elif velocity_stability == "variable":
            evidence.append(
                "Observed interval velocities varied under the evidence-quality rule."
            )
        elif velocity_stability == "unstable":
            evidence.append(
                "Observed interval velocities were unstable under the evidence-quality rule."
            )

        data_note = None
        if assessment_status == "not_assessed":
            data_note = "Evidence quality is not assessed because the forecast is unavailable."
        elif assessment_status == "not_applicable":
            data_note = "Evidence quality is not applicable because completion is directly observed."
        elif date_quality == "unusable":
            data_note = "No usable positive-day dated intervals were available for evidence assessment."

        return ForecastConfidence(
            assessment_status=assessment_status,
            level=level,
            total_snapshot_count=len(ordered),
            usable_observation_count=len(usable),
            missing_progress_count=missing_progress_count,
            interval_count=interval_count,
            valid_velocity_interval_count=valid_velocity_interval_count,
            zero_day_gap_count=zero_day_gap_count,
            positive_interval_count=positive_interval_count,
            zero_interval_count=zero_interval_count,
            negative_interval_count=negative_interval_count,
            velocity_stability=velocity_stability,
            direction_consistency=direction_consistency,
            date_quality=date_quality,
            evidence=evidence,
            data_note=data_note,
        )

    @staticmethod
    def _classify_stability(values: list[float]) -> str:
        if len(values) < 2:
            return "not_assessable"

        average = mean(values)
        if not math.isfinite(average) or average <= 0:
            return "not_assessable"

        coefficient_of_variation = pstdev(values) / average
        if not math.isfinite(coefficient_of_variation):
            return "not_assessable"
        if coefficient_of_variation <= 0.25 or math.isclose(
            coefficient_of_variation,
            0.25,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            return "stable"
        if coefficient_of_variation <= 0.75 or math.isclose(
            coefficient_of_variation,
            0.75,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            return "variable"
        return "unstable"

    @staticmethod
    def _assess_level(
        forecast: ForecastResult,
        *,
        usable_count: int,
        missing_progress_count: int,
        velocity_stability: str,
        direction_consistency: str,
        zero_day_gap_count: int,
        stability_velocity_count: int,
    ) -> tuple[str, str | None]:
        if forecast.status in {"insufficient_data", "unavailable"}:
            return "not_assessed", None
        if forecast.current_progress == 100:
            return "not_applicable", None

        if direction_consistency == "non_positive":
            return "assessed", "low"
        if velocity_stability == "unstable":
            return "assessed", "low"

        level = "low"
        if (
            usable_count >= 3
            and velocity_stability == "stable"
            and direction_consistency == "positive"
        ):
            level = "medium"

        if (
            usable_count >= 5
            and missing_progress_count == 0
            and stability_velocity_count >= 2
            and zero_day_gap_count == 0
            and velocity_stability == "stable"
            and direction_consistency == "positive"
        ):
            level = "high"

        if missing_progress_count or zero_day_gap_count:
            level = min(level, "medium", key=("low", "medium", "high").index)
        if velocity_stability in {"not_assessable", "variable"}:
            level = min(level, "medium", key=("low", "medium", "high").index)
        if direction_consistency == "mixed":
            level = min(level, "medium", key=("low", "medium", "high").index)

        return "assessed", level
