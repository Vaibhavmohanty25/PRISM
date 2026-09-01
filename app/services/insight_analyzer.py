from app.schemas.project_data import (
    ActivityHistory,
    ActivityInsight,
    InsightFinding,
    ProjectInsight,
    RiskResult,
    TrendResult,
)
from app.services.progress_tracker import ProgressTracker
from app.services.risk_analyzer import RiskAnalyzer
from app.services.trend_analyzer import TrendAnalyzer


FINDING_PRIORITIES = {
    "declining_progress": "high",
    "stalled_activity": "medium",
    "low_velocity": "medium",
    "repeated_delay": "medium",
    "repeated_issue": "medium",
}


class InsightAnalyzer:
    """Build deterministic explanations from existing trend and risk results."""

    def __init__(
        self,
        tracker: ProgressTracker,
        trend_analyzer: TrendAnalyzer,
        risk_analyzer: RiskAnalyzer,
    ) -> None:
        self.tracker = tracker
        self.trend_analyzer = trend_analyzer
        self.risk_analyzer = risk_analyzer

    def _finding(
        self,
        finding_type: str,
        title: str,
        explanation: str,
        factual_evidence: list[str],
        recommendation: str,
    ) -> InsightFinding:
        return InsightFinding(
            finding_type=finding_type,
            priority=FINDING_PRIORITIES[finding_type],
            title=title,
            explanation=explanation,
            factual_evidence=factual_evidence,
            recommendation=recommendation,
        )

    def _findings(
        self,
        trend_result: TrendResult,
        risk_result: RiskResult,
    ) -> list[InsightFinding]:
        findings: list[InsightFinding] = []

        if trend_result.trend == "declining":
            findings.append(
                self._finding(
                    "declining_progress",
                    "Progress is declining",
                    "Progress decreased across the available reporting history.",
                    [
                        (
                            f"Progress changed from {trend_result.first_progress:g}% "
                            f"to {trend_result.last_progress:g}% across the available history."
                        )
                    ],
                    "Review the causes of regression and agree corrective actions.",
                )
            )
        elif trend_result.trend == "stalled":
            findings.append(
                self._finding(
                    "stalled_activity",
                    "Progress has stalled",
                    "Progress changes remained within the configured stall threshold.",
                    [
                        (
                            f"Average progress change was "
                            f"{trend_result.average_progress_delta:g} percentage points."
                        )
                    ],
                    "Review blockers and confirm the next recovery action.",
                )
            )

        if (
            trend_result.average_velocity_per_day is not None
            and "Progress velocity is very low" in risk_result.risk_signals
        ):
            findings.append(
                self._finding(
                    "low_velocity",
                    "Progress velocity is very low",
                    "The observed progress velocity is below the existing risk threshold.",
                    [
                        (
                            "Average velocity was "
                            f"{trend_result.average_velocity_per_day:g} percentage points per day."
                        )
                    ],
                    "Review whether blockers or resources are limiting progress velocity.",
                )
            )

        for delay in sorted(
            risk_result.repeated_delays,
            key=str.casefold,
        ):
            findings.append(
                self._finding(
                    "repeated_delay",
                    f"Repeated delay: {delay}",
                    "The same delay reason was recorded in multiple snapshots.",
                    [f"Repeated delay reason: {delay}"],
                    "Assign an owner to address the recurring delay cause.",
                )
            )

        for issue in sorted(
            risk_result.repeated_issues,
            key=str.casefold,
        ):
            findings.append(
                self._finding(
                    "repeated_issue",
                    f"Repeated issue: {issue}",
                    "The same issue was recorded in multiple snapshots.",
                    [f"Repeated issue: {issue}"],
                    "Track the recurring issue until it is resolved.",
                )
            )

        return findings

    def analyze_history(
        self,
        history: ActivityHistory,
    ) -> ActivityInsight:
        trend_result = self.trend_analyzer.analyze_history(history)
        risk_result = self.risk_analyzer.analyze_history(history)

        if trend_result.trend == "insufficient_data":
            return ActivityInsight(
                project_name=history.project_name,
                activity_name=history.activity_name,
                status="insufficient_data",
                risk_level=risk_result.risk_level,
                risk_score=risk_result.risk_score,
                trend=trend_result.trend,
                findings=[],
                data_note=(
                    "At least two usable progress observations are required "
                    "to produce findings."
                ),
            )

        return ActivityInsight(
            project_name=history.project_name,
            activity_name=history.activity_name,
            status="available",
            risk_level=risk_result.risk_level,
            risk_score=risk_result.risk_score,
            trend=trend_result.trend,
            findings=self._findings(trend_result, risk_result),
        )

    def analyze_activity(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityInsight | None:
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
    ) -> ProjectInsight | None:
        if project_name not in self.tracker.get_projects():
            return None

        histories = self.tracker.get_all_histories(project_name)
        return ProjectInsight(
            project_name=histories[0].project_name if histories else project_name or "",
            activities=[
                self.analyze_history(history)
                for history in histories
            ],
        )
