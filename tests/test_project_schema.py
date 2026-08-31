from app.schemas.project_data import (
    ProgressReport,
    ActivityProgress,
    ExtractionMetadata
)


def test_progress_report():

    activity = ActivityProgress(
        activity_name="Foundation Work",
        quantity_completed=120,
        unit="m3",
        progress_percentage=70,
        status="In Progress",
        issues=["Heavy rainfall"],
        delay_reason="Heavy rainfall",
        delay_duration_hours=3
    )

    report = ProgressReport(
        project_name="Metro Construction Project",
        location="Block A",
        activities=[activity],
        extraction_metadata=ExtractionMetadata(
            confidence_score=0.92
        )
    )

    assert report.activities[0].activity_name == "Foundation Work"
    assert report.activities[0].progress_percentage == 70
    assert report.extraction_metadata.confidence_score == 0.92