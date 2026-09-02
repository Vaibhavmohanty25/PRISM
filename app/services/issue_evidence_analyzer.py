from app.schemas.project_data import (
    ActivityIssueHistory,
    ActivityHistory,
    IssueObservation,
    ProjectIssueHistory,
)
from app.services.progress_tracker import ProgressTracker
from app.services.trend_analyzer import _ordered_snapshots


class IssueEvidenceAnalyzer:
    """Deterministic projections of explicitly reported issue observations."""

    def __init__(self, tracker: ProgressTracker) -> None:
        self.tracker = tracker

    def history_for_activity(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityIssueHistory | None:
        history = self.tracker.get_activity_history(
            project_name,
            activity_name,
        )

        if history is None:
            return None

        observations = []

        for snapshot in _ordered_snapshots(history.snapshots):
            for issue in snapshot.issues:
                if issue is None:
                    continue

                normalized_issue = issue.strip()

                if not normalized_issue:
                    continue

                observations.append(
                    IssueObservation(
                        report_date=snapshot.report_date,
                        issue=normalized_issue,
                        submission_order=snapshot.submission_order,
                    )
                )

        return ActivityIssueHistory(
            project_name=history.project_name,
            activity_name=history.activity_name,
            observations=observations,
        )

    def history_for_project(
        self,
        project_name: str | None,
    ) -> ProjectIssueHistory | None:
        if project_name not in self.tracker.get_projects():
            return None

        activities = []

        for history in self.tracker.get_all_histories(project_name):
            activity_history = self.history_for_activity(
                project_name,
                history.activity_name,
            )

            if activity_history is not None:
                activities.append(activity_history)

        return ProjectIssueHistory(
            project_name=project_name or "",
            activities=activities,
        )
