from app.schemas.project_data import (
    ActivityProgress,
    ExtractionConfidence,
)


def calculate_activity_confidence(
    activity: ActivityProgress,
) -> ExtractionConfidence:

    scores = {}

    # Progress
    if activity.progress_percentage is not None:
        scores["progress"] = (
            1.0
            if activity.evidence
            and activity.evidence.progress
            else 0.5
        )

    # Quantity
    if activity.quantity_completed is not None:
        scores["quantity"] = (
            1.0
            if activity.evidence
            and activity.evidence.quantity
            else 0.5
        )

    # Status
    if activity.status is not None:
        scores["status"] = (
            1.0
            if activity.evidence
            and activity.evidence.status
            else 0.5
        )

    # Delay
    if (
        activity.delay_reason is not None
        or activity.delay_duration_hours is not None
    ):
        scores["delay"] = (
            1.0
            if activity.evidence
            and activity.evidence.delay
            else 0.5
        )

    if scores:
        overall = sum(scores.values()) / len(scores)
    else:
        overall = 0.0

    return ExtractionConfidence(
        progress=scores.get("progress"),
        quantity=scores.get("quantity"),
        status=scores.get("status"),
        delay=scores.get("delay"),
        overall=round(overall, 2),
    )