import math

from app.schemas.project_data import (
    ForecastResult,
    PredictiveRisk,
)


class PredictiveRiskAnalyzer:
    """Classify future trajectory risk from an existing forecast result."""

    def analyze(self, forecast: ForecastResult) -> PredictiveRisk:
        confidence = forecast.confidence
        evidence: list[str] = []

        current_progress = forecast.current_progress
        if not self._valid_progress(current_progress):
            return self._result(
                forecast,
                level="not_assessed",
                data_note=(
                    "Predictive risk was not assessed because current "
                    "progress was outside the valid range."
                ),
            )

        if current_progress == 100:
            return self._result(
                forecast,
                level="not_applicable",
                evidence=[
                    "Activity is complete at 100% observed progress."
                ],
            )

        if confidence is None:
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because forecast evidence quality was unavailable.",
            )

        if forecast.status == "insufficient_data":
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because sufficient usable progress evidence was unavailable.",
            )

        direction = confidence.direction_consistency
        stability = confidence.velocity_stability

        if forecast.status == "unavailable":
            if (
                self._non_positive_velocity(
                    forecast.historical_velocity_per_day
                )
                and direction == "non_positive"
            ):
                return self._result(
                    forecast,
                    level="high",
                    evidence=[
                        "Observed trajectory contains no positive progress movement."
                    ],
                )

            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because no usable temporal trajectory evidence was available.",
            )

        if confidence.assessment_status != "assessed":
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because trajectory evidence was internally inconsistent.",
            )

        if confidence.date_quality != "complete":
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because no usable temporal trajectory evidence was available.",
            )

        if confidence.valid_velocity_interval_count <= 0:
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because no usable temporal trajectory evidence was available.",
            )

        if direction == "non_positive":
            if stability == "not_assessable":
                if not self._non_positive_velocity(
                    forecast.historical_velocity_per_day
                ):
                    return self._not_assessed(
                        forecast,
                        "Predictive risk was not assessed because velocity stability was not assessable.",
                    )
            return self._result(
                forecast,
                level="high",
                evidence=[
                    "Observed trajectory contains no positive progress movement."
                ],
            )

        if direction not in {"positive", "mixed"}:
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because trajectory direction was not assessable.",
            )

        if stability == "not_assessable":
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because velocity stability was not assessable.",
            )

        if direction == "positive" and stability == "stable":
            level = "low"
        elif direction == "mixed" and stability == "unstable":
            level = "high"
        elif direction in {"positive", "mixed"} and stability in {
            "variable",
            "unstable",
        }:
            level = "medium"
        elif direction == "mixed" and stability == "stable":
            level = "medium"
        else:
            return self._not_assessed(
                forecast,
                "Predictive risk was not assessed because trajectory evidence was internally inconsistent.",
            )

        if direction == "positive":
            evidence.append(
                "Observed trajectory shows consistent positive progress movement."
            )
        else:
            evidence.append(
                "Observed trajectory contains both positive and non-positive progress movement."
            )

        if stability == "variable":
            evidence.append("Observed progress velocity is variable.")
        elif stability == "unstable":
            evidence.append("Observed progress velocity is unstable.")

        if confidence.missing_progress_count:
            evidence.append(
                "Some progress snapshots lacked usable progress and were excluded from trajectory evidence."
            )

        return self._result(
            forecast,
            level=level,
            evidence=evidence,
        )

    @staticmethod
    def _valid_progress(value: float | None) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and 0 <= value <= 100
        )

    @staticmethod
    def _non_positive_velocity(value: float | None) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value <= 0
        )

    @staticmethod
    def _result(
        forecast: ForecastResult,
        *,
        level: str,
        evidence: list[str] | None = None,
        data_note: str | None = None,
    ) -> PredictiveRisk:
        return PredictiveRisk(
            project_name=forecast.project_name,
            activity_name=forecast.activity_name,
            level=level,
            evidence=evidence or [],
            data_note=data_note,
        )

    @classmethod
    def _not_assessed(
        cls,
        forecast: ForecastResult,
        data_note: str,
    ) -> PredictiveRisk:
        return cls._result(
            forecast,
            level="not_assessed",
            data_note=data_note,
        )
