from fastapi import Request

from app.schemas.project_data import (
    ActivityPredictiveSummary,
    ActivityInsight,
    ActivityHistory,
    DecisionSupport,
    DecisionSupportPriorityDistribution,
    DecisionSupportStatusDistribution,
    ConfidenceLevelDistribution,
    ForecastResult,
    ForecastStatusDistribution,
    ActivityScheduleImpact,
    ActivityScheduleImpactHistory,
    ActivityIssueHistory,
    PredictiveRiskDistribution,
    ProjectPredictiveActivity,
    ProjectPredictiveSummary,
    ProjectInsight,
    ProjectIssueHistory,
    ProjectScheduleImpact,
    ProjectScheduleImpactHistory,
    ProgressReport,
    RiskResult,
    TrendResult,
)
from app.services.progress_tracker import ProgressTracker
from app.services.risk_analyzer import RiskAnalyzer
from app.services.insight_analyzer import InsightAnalyzer
from app.services.issue_evidence_analyzer import IssueEvidenceAnalyzer
from app.services.schedule_impact_analyzer import ScheduleImpactAnalyzer
from app.services.trend_analyzer import TrendAnalyzer
from app.services.forecast_analyzer import ForecastAnalyzer
from app.services.forecast_confidence_analyzer import ForecastConfidenceAnalyzer
from app.services.predictive_risk_analyzer import PredictiveRiskAnalyzer
from app.services.decision_support_analyzer import DecisionSupportAnalyzer


class AnalysisService:
    """Application boundary for recording and analyzing validated reports."""

    def __init__(self, tracker: ProgressTracker | None = None) -> None:
        self.tracker = tracker or ProgressTracker()
        self.trend_analyzer = TrendAnalyzer(self.tracker)
        self.forecast_analyzer = ForecastAnalyzer(self.tracker)
        self.forecast_confidence_analyzer = ForecastConfidenceAnalyzer()
        self.predictive_risk_analyzer = PredictiveRiskAnalyzer()
        self.decision_support_analyzer = DecisionSupportAnalyzer()
        self.risk_analyzer = RiskAnalyzer(self.tracker)
        self.insight_analyzer = InsightAnalyzer(
            self.tracker,
            self.trend_analyzer,
            self.risk_analyzer,
        )
        self.schedule_impact_analyzer = ScheduleImpactAnalyzer(
            self.tracker,
        )
        self.issue_evidence_analyzer = IssueEvidenceAnalyzer(
            self.tracker,
        )

    def record_report(self, report: ProgressReport) -> None:
        self.tracker.record(report)

    def get_projects(self) -> list[str]:
        return self.tracker.get_projects()

    def has_project(self, project_name: str | None) -> bool:
        return self.tracker.has_project(project_name)

    def get_activity_history(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityHistory | None:
        return self.tracker.get_activity_history(
            project_name,
            activity_name,
        )

    def analyze_activity_trend(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> TrendResult | None:
        return self.trend_analyzer.analyze_activity(
            project_name,
            activity_name,
        )

    def analyze_project_trends(
        self,
        project_name: str | None,
    ) -> list[TrendResult]:
        return self.trend_analyzer.analyze_project(project_name)

    def analyze_activity_forecast(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ForecastResult | None:
        forecast = self.forecast_analyzer.analyze_activity(
            project_name,
            activity_name,
        )
        if forecast is None:
            return None

        history = self.tracker.get_activity_history(
            project_name,
            activity_name,
        )
        if history is None:
            return forecast

        confidence = self.forecast_confidence_analyzer.analyze_history(
            history,
            forecast,
        )
        composed = forecast.model_copy(update={"confidence": confidence})
        predictive_risk = self.predictive_risk_analyzer.analyze(composed)
        composed = composed.model_copy(
            update={"predictive_risk": predictive_risk}
        )
        return composed

    def analyze_activity_predictive_summary(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityPredictiveSummary | None:
        forecast = self.analyze_activity_forecast(
            project_name,
            activity_name,
        )
        if forecast is None:
            return None

        decision_support = self._analyze_decision_support_from_forecast(
            project_name,
            activity_name,
            forecast,
        )
        if decision_support is None:
            return None

        return ActivityPredictiveSummary(
            project_name=forecast.project_name,
            activity_name=forecast.activity_name,
            forecast=forecast,
            decision_support=decision_support,
        )

    def _analyze_decision_support_from_forecast(
        self,
        project_name: str | None,
        activity_name: str,
        forecast: ForecastResult,
    ) -> DecisionSupport | None:
        history = self.tracker.get_activity_history(
            project_name,
            activity_name,
        )
        if history is None:
            return None

        trend_result = self.trend_analyzer.analyze_history(history)
        risk_result = self.risk_analyzer.analyze_history(history)
        schedule_impact = self.schedule_impact_analyzer.analyze_history(
            history
        )
        issue_history = self.issue_evidence_analyzer.history_for_activity(
            project_name,
            activity_name,
        )
        return self.decision_support_analyzer.analyze(
            trend_result,
            risk_result,
            forecast,
            schedule_impact,
            issue_history,
        )

    def analyze_activity_decision_support(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> DecisionSupport | None:
        forecast = self.analyze_activity_forecast(
            project_name,
            activity_name,
        )
        if forecast is None:
            return None

        return self._analyze_decision_support_from_forecast(
            project_name,
            activity_name,
            forecast,
        )

    def analyze_activity_risk(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> RiskResult | None:
        return self.risk_analyzer.analyze_activity(
            project_name,
            activity_name,
        )

    def analyze_project_risks(
        self,
        project_name: str | None,
    ) -> list[RiskResult]:
        return self.risk_analyzer.analyze_project(project_name)

    def analyze_activity_insight(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityInsight | None:
        return self.insight_analyzer.analyze_activity(
            project_name,
            activity_name,
        )

    def analyze_project_insight(
        self,
        project_name: str | None,
    ) -> ProjectInsight | None:
        return self.insight_analyzer.analyze_project(project_name)

    def analyze_activity_schedule_impact(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityScheduleImpact | None:
        return self.schedule_impact_analyzer.analyze_activity(
            project_name,
            activity_name,
        )

    def analyze_activity_schedule_impact_history(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityScheduleImpactHistory | None:
        return self.schedule_impact_analyzer.history_for_activity(
            project_name,
            activity_name,
        )

    def analyze_project_schedule_impact_history(
        self,
        project_name: str | None,
    ) -> ProjectScheduleImpactHistory | None:
        return self.schedule_impact_analyzer.history_for_project(
            project_name,
        )

    def analyze_project_schedule_impact(
        self,
        project_name: str | None,
    ) -> ProjectScheduleImpact | None:
        return self.schedule_impact_analyzer.analyze_project(
            project_name,
        )

    def analyze_activity_issue_history(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityIssueHistory | None:
        return self.issue_evidence_analyzer.history_for_activity(
            project_name,
            activity_name,
        )

    def analyze_project_issue_history(
        self,
        project_name: str | None,
    ) -> ProjectIssueHistory | None:
        return self.issue_evidence_analyzer.history_for_project(
            project_name,
        )

    def analyze_project_predictive_summary(
        self,
        project_name: str | None,
    ) -> ProjectPredictiveSummary | None:
        if not self.has_project(project_name):
            return None

        histories = self.tracker.get_all_histories(project_name)
        references: list[tuple[ProjectPredictiveActivity, bool, bool]] = []

        for history in histories:
            forecast = self.analyze_activity_forecast(
                project_name,
                history.activity_name,
            )
            trend = self.trend_analyzer.analyze_history(history)
            risk = self.risk_analyzer.analyze_history(history)
            schedule_impact = self.schedule_impact_analyzer.analyze_history(
                history
            )
            issue_history = self.issue_evidence_analyzer.history_for_activity(
                project_name,
                history.activity_name,
            )
            decision_support = self.decision_support_analyzer.analyze(
                trend,
                risk,
                forecast,
                schedule_impact,
                issue_history,
            )

            reference, completed, insufficient = self._project_predictive_activity(
                history.activity_name,
                forecast,
                decision_support,
            )
            references.append((reference, completed, insufficient))

        ordered_references = [item[0] for item in references]
        attention = [
            reference
            for reference, completed, _ in references
            if not completed
            and reference.decision_support_response
            in {"investigate", "review", "verify_data"}
        ]
        insufficient = [
            reference
            for reference, completed, is_insufficient in references
            if not completed and is_insufficient
        ]
        attention.sort(key=self._attention_sort_key)
        insufficient.sort(key=self._insufficient_sort_key)

        return ProjectPredictiveSummary(
            project_name=(
                histories[0].project_name
                if histories
                else project_name or ""
            ),
            total_activity_count=len(ordered_references),
            active_activity_count=sum(
                not completed for _, completed, _ in references
            ),
            completed_activity_count=sum(
                completed for _, completed, _ in references
            ),
            forecast_status_distribution=ForecastStatusDistribution(
                **self._count_values(
                    ordered_references,
                    "forecast_status",
                    ("available", "insufficient_data", "unavailable"),
                )
            ),
            confidence_level_distribution=ConfidenceLevelDistribution(
                **self._confidence_counts(ordered_references)
            ),
            predictive_risk_distribution=PredictiveRiskDistribution(
                **self._count_values(
                    ordered_references,
                    "predictive_risk_level",
                    ("low", "medium", "high", "not_assessed", "not_applicable"),
                )
            ),
            decision_support_status_distribution=DecisionSupportStatusDistribution(
                **self._count_values(
                    ordered_references,
                    "decision_support_status",
                    ("supported", "review_only", "insufficient_evidence", "not_applicable"),
                )
            ),
            decision_support_priority_distribution=DecisionSupportPriorityDistribution(
                **self._count_values(
                    ordered_references,
                    "decision_support_priority",
                    ("none", "low", "medium", "high"),
                )
            ),
            activities_requiring_attention=attention,
            activities_with_insufficient_evidence=insufficient,
            evidence_limitations=self._summary_limitations(
                references
            ),
        )

    @staticmethod
    def _project_predictive_activity(
        activity_name: str,
        forecast: ForecastResult | None,
        decision_support: DecisionSupport,
    ) -> tuple[ProjectPredictiveActivity, bool, bool]:
        confidence = forecast.confidence if forecast is not None else None
        predictive_risk = (
            forecast.predictive_risk
            if forecast is not None
            else None
        )
        completed = (
            forecast is not None
            and forecast.current_progress == 100
        )
        confidence_status = (
            confidence.assessment_status
            if confidence is not None
            else "not_assessed"
        )
        confidence_level = (
            confidence.level
            if confidence is not None
            else None
        )
        predictive_level = (
            predictive_risk.level
            if predictive_risk is not None
            else "not_assessed"
        )
        forecast_status = (
            forecast.status
            if forecast is not None
            else "unavailable"
        )

        limitations: list[str] = list(decision_support.limitations)
        if forecast is None:
            limitations.append("No forecast result was available.")
        else:
            if forecast.data_note:
                limitations.append(forecast.data_note)
            if confidence is not None and confidence.data_note:
                limitations.append(confidence.data_note)
            if predictive_risk is not None and predictive_risk.data_note:
                limitations.append(predictive_risk.data_note)

        limitations = AnalysisService._deduplicate(limitations)
        insufficient = (
            forecast is None
            or forecast.status != "available"
            or confidence is None
            or confidence.assessment_status == "not_assessed"
            or predictive_level == "not_assessed"
            or decision_support.status == "insufficient_evidence"
        )

        reference = ProjectPredictiveActivity(
            activity_name=activity_name,
            forecast_status=forecast_status,
            confidence_assessment_status=confidence_status,
            confidence_level=confidence_level,
            predictive_risk_level=predictive_level,
            decision_support_status=decision_support.status,
            decision_support_priority=decision_support.priority,
            decision_support_response=decision_support.response,
            decision_support_trigger=decision_support.trigger,
            limitations=limitations,
        )
        return reference, completed, insufficient

    @staticmethod
    def _count_values(
        references: list[ProjectPredictiveActivity],
        field: str,
        keys: tuple[str, ...],
        *,
        fallback: str | None = None,
    ) -> dict[str, int]:
        counts = {key: 0 for key in keys}
        for reference in references:
            value = getattr(reference, field)
            if value is None and fallback is not None:
                value = fallback
            if value in counts:
                counts[value] += 1
        return counts

    @staticmethod
    def _confidence_counts(
        references: list[ProjectPredictiveActivity],
    ) -> dict[str, int]:
        counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "not_assessed": 0,
            "not_applicable": 0,
        }
        for reference in references:
            if reference.confidence_assessment_status == "not_applicable":
                counts["not_applicable"] += 1
            elif (
                reference.confidence_assessment_status == "not_assessed"
                or reference.confidence_level is None
            ):
                counts["not_assessed"] += 1
            else:
                counts[reference.confidence_level] += 1
        return counts

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value and value not in result:
                result.append(value)
        return result

    @classmethod
    def _summary_limitations(
        cls,
        references: list[tuple[ProjectPredictiveActivity, bool, bool]],
    ) -> list[str]:
        limitations: list[str] = []
        for reference, completed, _ in references:
            if completed:
                continue
            limitations.extend(reference.limitations)
        return cls._deduplicate(limitations)

    @staticmethod
    def _attention_sort_key(
        reference: ProjectPredictiveActivity,
    ) -> tuple[int, int, int, str]:
        return (
            {"high": 0, "medium": 1, "low": 2, "none": 3}[
                reference.decision_support_priority
            ],
            {
                "investigate": 0,
                "review": 1,
                "verify_data": 2,
                "monitor": 3,
                "none": 4,
            }[reference.decision_support_response],
            {
                "high": 0,
                "medium": 1,
                "low": 2,
                "not_assessed": 3,
                "not_applicable": 4,
            }[reference.predictive_risk_level],
            reference.activity_name.casefold(),
        )

    @staticmethod
    def _insufficient_sort_key(
        reference: ProjectPredictiveActivity,
    ) -> tuple[int, int, int, int, str]:
        return (
            {
                "unavailable": 0,
                "insufficient_data": 1,
                "available": 2,
            }[reference.forecast_status],
            {
                "not_assessed": 0,
                "assessed": 1,
                "not_applicable": 2,
            }[reference.confidence_assessment_status],
            {
                "not_assessed": 0,
                "high": 1,
                "medium": 2,
                "low": 3,
                "not_applicable": 4,
            }[reference.predictive_risk_level],
            {"high": 0, "medium": 1, "low": 2, "none": 3}[
                reference.decision_support_priority
            ],
            reference.activity_name.casefold(),
        )


def get_analysis_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service
