from fastapi import Request

from app.schemas.project_data import (
    ActivityInsight,
    ActivityHistory,
    ActivityScheduleImpact,
    ProjectInsight,
    ProjectScheduleImpact,
    ProgressReport,
    RiskResult,
    TrendResult,
)
from app.services.progress_tracker import ProgressTracker
from app.services.risk_analyzer import RiskAnalyzer
from app.services.insight_analyzer import InsightAnalyzer
from app.services.schedule_impact_analyzer import ScheduleImpactAnalyzer
from app.services.trend_analyzer import TrendAnalyzer


class AnalysisService:
    """Application boundary for recording and analyzing validated reports."""

    def __init__(self, tracker: ProgressTracker | None = None) -> None:
        self.tracker = tracker or ProgressTracker()
        self.trend_analyzer = TrendAnalyzer(self.tracker)
        self.risk_analyzer = RiskAnalyzer(self.tracker)
        self.insight_analyzer = InsightAnalyzer(
            self.tracker,
            self.trend_analyzer,
            self.risk_analyzer,
        )
        self.schedule_impact_analyzer = ScheduleImpactAnalyzer(
            self.tracker,
        )

    def record_report(self, report: ProgressReport) -> None:
        self.tracker.record(report)

    def get_projects(self) -> list[str]:
        return self.tracker.get_projects()

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

    def analyze_project_schedule_impact(
        self,
        project_name: str | None,
    ) -> ProjectScheduleImpact | None:
        return self.schedule_impact_analyzer.analyze_project(
            project_name,
        )


def get_analysis_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service
