import pytest

from app.schemas.project_data import (
    ProgressReport,
    ActivityProgress,
    ExtractionMetadata
)


@pytest.mark.parametrize("value", [True, False])
def test_boolean_progress_percentage_is_invalid(value):
    with pytest.raises(ValueError):
        ActivityProgress(
            activity_name="Foundation Work",
            progress_percentage=value,
        )


@pytest.mark.parametrize("value", [0, 1, 50, 100])
def test_numeric_progress_percentage_values_remain_valid(value):
    activity = ActivityProgress(
        activity_name="Foundation Work",
        progress_percentage=value,
    )

    assert activity.progress_percentage == value


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
