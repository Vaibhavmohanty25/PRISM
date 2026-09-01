import json
from typing import Any

from app.schemas.project_data import (
    ActivityHistory,
    ActivitySnapshot,
    ProgressReport,
)

UNASSIGNED_PROJECT = "__unassigned__"


def normalize_activity_name(
    activity_name: str,
) -> str:
    return activity_name.strip().lower()


def project_key(
    project_name: str | None,
) -> str:
    if not project_name or not project_name.strip():
        return UNASSIGNED_PROJECT

    return project_name.strip()


class ProgressTracker:
    """
    In-memory store for historical activity progress snapshots.

    Consumes validated ProgressReport objects without modifying
    the Phase 1 extraction pipeline.
    """

    def __init__(self) -> None:
        self._activities: dict[
            str,
            dict[str, dict[str, object]],
        ] = {}
        self._submission_counters: dict[str, int] = {}
        self._recorded_snapshot_keys: set[tuple[str, ...]] = set()

    @staticmethod
    def _report_identity(
        report: ProgressReport,
    ) -> tuple[str, ...]:
        payload = report.model_dump(
            mode="json",
            exclude={"extraction_metadata"},
        )
        canonical_payload = ProgressTracker._canonicalize(payload)

        return (
            json.dumps(
                canonical_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
        )

    @staticmethod
    def _canonicalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: ProgressTracker._canonicalize(item)
                for key, item in sorted(value.items())
            }

        if isinstance(value, list):
            canonical_items = [
                ProgressTracker._canonicalize(item)
                for item in value
            ]
            return sorted(
                canonical_items,
                key=lambda item: json.dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ),
            )

        if isinstance(value, str):
            return value.strip().casefold()

        return value

    def record(
        self,
        report: ProgressReport,
    ) -> None:
        key = project_key(report.project_name)

        if key not in self._activities:
            self._activities[key] = {}
            self._submission_counters[key] = 0

        self._submission_counters[key] += 1
        submission_order = self._submission_counters[key]

        report_identity = self._report_identity(report)

        for activity in report.activities:
            if not activity.activity_name:
                continue

            display_name = activity.activity_name.strip()
            activity_key = normalize_activity_name(
                display_name
            )

            snapshot_key = report_identity + (activity_key,)

            if snapshot_key in self._recorded_snapshot_keys:
                continue

            self._recorded_snapshot_keys.add(snapshot_key)

            snapshot = ActivitySnapshot(
                report_date=report.report_date,
                submission_order=submission_order,
                progress_percentage=(
                    activity.progress_percentage
                ),
                quantity_completed=(
                    activity.quantity_completed
                ),
                unit=activity.unit,
                status=activity.status,
                issues=list(activity.issues),
                delay_reason=activity.delay_reason,
                delay_duration_hours=(
                    activity.delay_duration_hours
                ),
            )

            project_activities = self._activities[key]

            if activity_key not in project_activities:
                project_activities[activity_key] = {
                    "display_name": display_name,
                    "snapshots": [],
                }

            project_activities[activity_key][
                "snapshots"
            ].append(snapshot)

    def get_projects(self) -> list[str]:
        return sorted(self._activities.keys())

    def get_activity_history(
        self,
        project_name: str | None,
        activity_name: str,
    ) -> ActivityHistory | None:
        key = project_key(project_name)
        activity_key = normalize_activity_name(
            activity_name
        )

        project_activities = self._activities.get(key)
        if not project_activities:
            return None

        entry = project_activities.get(activity_key)
        if not entry:
            return None

        return ActivityHistory(
            project_name=key,
            activity_name=entry["display_name"],
            snapshots=list(entry["snapshots"]),
        )

    def get_all_histories(
        self,
        project_name: str | None,
    ) -> list[ActivityHistory]:
        key = project_key(project_name)
        project_activities = self._activities.get(key)

        if not project_activities:
            return []

        histories = []

        for entry in project_activities.values():
            histories.append(
                ActivityHistory(
                    project_name=key,
                    activity_name=entry["display_name"],
                    snapshots=list(entry["snapshots"]),
                )
            )

        histories.sort(
            key=lambda history: (
                history.activity_name.lower()
            )
        )

        return histories
