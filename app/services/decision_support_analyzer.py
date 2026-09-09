from collections import Counter

from app.schemas.project_data import (
    ActivityIssueHistory,
    ActivityScheduleImpact,
    DecisionSupport,
    ForecastResult,
    RiskResult,
    TrendResult,
)


_VALID_RISK_LEVELS = {"low", "medium", "high"}


class DecisionSupportAnalyzer:
    """Classify bounded activity attention from existing analysis outputs."""

    def analyze(
        self,
        trend_result: TrendResult,
        risk_result: RiskResult | None,
        forecast_result: ForecastResult | None,
        schedule_impact: ActivityScheduleImpact | None,
        issue_history: ActivityIssueHistory | None,
    ) -> DecisionSupport:
        project_name = trend_result.project_name
        activity_name = trend_result.activity_name
        current_progress = (
            forecast_result.current_progress
            if forecast_result is not None
            else trend_result.last_progress
        )

        if current_progress == 100:
            return self._build(
                project_name,
                activity_name,
                status="not_applicable",
                priority="none",
                response="none",
                trigger="completion",
                rationale="The activity is complete, so decision support is not applicable.",
                forecast_result=forecast_result,
                risk_result=risk_result,
                schedule_impact=schedule_impact,
                issue_history=issue_history,
                completion=True,
            )

        observed_level = self._observed_level(risk_result)
        predictive_level = self._predictive_level(forecast_result)
        repeated_issues = self._repeated_issue_values(
            issue_history,
            risk_result,
        )
        repeated_delays = self._repeated_delay_values(
            risk_result,
            schedule_impact,
        )
        has_issue_evidence = bool(
            issue_history is not None and issue_history.observations
        )
        has_delay_evidence = bool(
            schedule_impact is not None
            and schedule_impact.delay_observation_count > 0
        )

        if observed_level == "high" and predictive_level == "high":
            status, priority, response, trigger = (
                "supported",
                "high",
                "investigate",
                "combined_evidence",
            )
            rationale = (
                "High observed and predictive risk classifications support "
                "bounded investigation."
            )
        elif observed_level == "high":
            status, priority, response, trigger = (
                "supported",
                "high",
                "investigate",
                "observed_risk",
            )
            rationale = (
                "The high observed-risk classification supports bounded "
                "investigation."
            )
        elif predictive_level == "high":
            status, priority, response, trigger = (
                "supported",
                "high",
                "review",
                "predictive_risk",
            )
            rationale = (
                "The high predictive-risk classification supports bounded "
                "review."
            )
        elif observed_level == "medium" or predictive_level == "medium":
            trigger = (
                "observed_risk"
                if observed_level == "medium"
                else "predictive_risk"
            )
            status, priority, response = "review_only", "medium", "review"
            rationale = (
                "A medium observed or predictive risk classification warrants "
                "bounded review."
            )
        elif repeated_issues or repeated_delays:
            status, priority, response, trigger = (
                "review_only",
                "medium",
                "investigate",
                "issue_evidence",
            )
            rationale = (
                "Repeated issue or delay evidence warrants bounded "
                "investigation without reclassifying predictive risk."
            )
        elif has_delay_evidence:
            status, priority, response, trigger = (
                "review_only",
                "medium",
                "review",
                "schedule_impact",
            )
            rationale = (
                "Explicit schedule-impact evidence warrants bounded review "
                "without inferring project slippage."
            )
        elif has_issue_evidence:
            status, priority, response, trigger = (
                "review_only",
                "low",
                "review",
                "issue_evidence",
            )
            rationale = "Isolated issue evidence warrants bounded review."
        elif observed_level == "low" and predictive_level == "low":
            status, priority, response, trigger = (
                "supported",
                "low",
                "monitor",
                "observed_risk",
            )
            rationale = (
                "Low observed and predictive risk classifications support "
                "bounded monitoring."
            )
        else:
            status, priority, response, trigger = (
                "insufficient_evidence",
                "none",
                "verify_data",
                "data_quality",
            )
            rationale = (
                "The available observed and predictive evidence is insufficient "
                "for a meaningful attention classification."
            )

        return self._build(
            project_name,
            activity_name,
            status=status,
            priority=priority,
            response=response,
            trigger=trigger,
            rationale=rationale,
            forecast_result=forecast_result,
            risk_result=risk_result,
            schedule_impact=schedule_impact,
            issue_history=issue_history,
            repeated_issues=repeated_issues,
            repeated_delays=repeated_delays,
        )

    @staticmethod
    def _observed_level(risk_result: RiskResult | None) -> str | None:
        if risk_result is None or risk_result.risk_level not in _VALID_RISK_LEVELS:
            return None
        return risk_result.risk_level

    @staticmethod
    def _predictive_level(
        forecast_result: ForecastResult | None,
    ) -> str | None:
        if forecast_result is None or forecast_result.predictive_risk is None:
            return None
        level = forecast_result.predictive_risk.level
        return level if level in _VALID_RISK_LEVELS else None

    @staticmethod
    def _repeated_issue_values(
        issue_history: ActivityIssueHistory | None,
        risk_result: RiskResult | None = None,
    ) -> list[str]:
        values: list[str] = []
        for issue in risk_result.repeated_issues if risk_result is not None else []:
            if issue not in values:
                values.append(issue)

        if issue_history is None:
            return values

        normalized_values: list[str] = []
        display_values: dict[str, str] = {}
        for observation in issue_history.observations:
            normalized = observation.issue.strip().casefold()
            if not normalized:
                continue
            normalized_values.append(normalized)
            display_values.setdefault(normalized, observation.issue.strip())

        counts = Counter(normalized_values)
        for normalized in normalized_values:
            if counts[normalized] >= 2 and display_values[normalized] not in values:
                values.append(display_values[normalized])
        return values

    @staticmethod
    def _repeated_delay_values(
        risk_result: RiskResult | None,
        schedule_impact: ActivityScheduleImpact | None,
    ) -> list[str]:
        values: list[str] = []
        for value in (
            risk_result.repeated_delays if risk_result is not None else []
        ) + (
            schedule_impact.repeated_delay_reasons
            if schedule_impact is not None
            else []
        ):
            if value not in values:
                values.append(value)
        return values

    def _build(
        self,
        project_name: str,
        activity_name: str,
        *,
        status: str,
        priority: str,
        response: str,
        trigger: str,
        rationale: str,
        forecast_result: ForecastResult | None,
        risk_result: RiskResult | None,
        schedule_impact: ActivityScheduleImpact | None,
        issue_history: ActivityIssueHistory | None,
        repeated_issues: list[str] | None = None,
        repeated_delays: list[str] | None = None,
        completion: bool = False,
    ) -> DecisionSupport:
        repeated_issues = repeated_issues or self._repeated_issue_values(
            issue_history,
            risk_result,
        )
        repeated_delays = repeated_delays or self._repeated_delay_values(
            risk_result,
            schedule_impact,
        )
        limitations = self._limitations(
            forecast_result,
            risk_result,
            schedule_impact,
            issue_history,
        )
        evidence = [
            (
                "Activity is complete; decision support is not applicable."
                if completion
                else f"Decision support status is {status}."
            ),
            f"Decision support trigger is {trigger}.",
        ]

        if risk_result is not None and self._observed_level(risk_result) is not None:
            evidence.append(
                f"Observed risk classification is {risk_result.risk_level}."
            )
            evidence.extend(risk_result.risk_signals)

        if (
            forecast_result is not None
            and forecast_result.predictive_risk is not None
            and self._predictive_level(forecast_result) is not None
        ):
            predictive = forecast_result.predictive_risk
            evidence.append(f"Predictive risk classification is {predictive.level}.")
            evidence.extend(predictive.evidence)

        if schedule_impact is not None and schedule_impact.delay_observation_count:
            evidence.append(schedule_impact.summary)
        if issue_history is not None and issue_history.observations:
            evidence.append(
                f"Issue evidence contains {len(issue_history.observations)} observation(s)."
            )
        if repeated_issues:
            evidence.append(
                "Repeated issue evidence: " + ", ".join(repeated_issues) + "."
            )
        if repeated_delays:
            evidence.append(
                "Repeated delay evidence: " + ", ".join(repeated_delays) + "."
            )

        evidence.extend(f"Data-quality limitation: {item}" for item in limitations)
        evidence.append(
            "Decision support is bounded to existing activity evidence and does not infer causes, deadlines, or operational actions."
        )

        return DecisionSupport(
            project_name=project_name,
            activity_name=activity_name,
            status=status,
            priority=priority,
            response=response,
            trigger=trigger,
            evidence=evidence,
            rationale=rationale,
            limitations=limitations,
        )

    @staticmethod
    def _limitations(
        forecast_result: ForecastResult | None,
        risk_result: RiskResult | None,
        schedule_impact: ActivityScheduleImpact | None,
        issue_history: ActivityIssueHistory | None,
    ) -> list[str]:
        limitations: list[str] = []

        if risk_result is None or risk_result.risk_level == "insufficient_data":
            limitations.append("Observed risk evidence was insufficient or unavailable.")

        if forecast_result is None:
            limitations.append("No forecast result was available.")
        else:
            if forecast_result.status != "available":
                limitations.append(
                    f"The forecast status was {forecast_result.status}."
                )
            predictive = forecast_result.predictive_risk
            if predictive is None or predictive.level not in _VALID_RISK_LEVELS:
                limitations.append("No valid predictive trajectory evidence was available.")

            confidence = forecast_result.confidence
            if confidence is None or confidence.assessment_status != "assessed":
                limitations.append("Predictive-risk confidence was not assessed.")
            elif confidence.level in {"low", "medium"}:
                limitations.append(
                    "Forecast evidence quality is "
                    f"{confidence.level}; it does not alter predictive-risk classification."
                )
            if confidence is not None and confidence.missing_progress_count:
                limitations.append("Some progress observations lacked usable progress.")
            if confidence is not None and confidence.zero_day_gap_count:
                limitations.append("Some observations occurred on the same day.")
            if confidence is not None and confidence.date_quality == "unusable":
                limitations.append("Forecast dates were unusable for temporal evidence.")

        if schedule_impact is None or schedule_impact.status == "insufficient_data":
            limitations.append("No schedule-impact evidence was available.")
        if issue_history is None or not issue_history.observations:
            limitations.append("No issue observations were provided.")

        return limitations
