from app.core.config import settings
from app.services.extraction_service import ExtractionService


def test_gemini_extraction():

    service = ExtractionService(
        settings.GEMINI_API_KEY
    )

    source_text = """
    Daily Progress Report

    Project: Delhi Metro Extension
    Date: 5 June 2025
    Location: Block A

    Foundation RCC work is 70 percent complete.
    120 cubic meters of concrete were completed.

    Heavy rainfall delayed the work by 3 hours.

    The activity is currently in progress.
    """

    result = service.extract_progress_report(
        source_text
    )

    print("\nExtracted result:")
    print(
        result.model_dump_json(
            indent=2
        )
    )

    # ---------------------------------------------
    # Metadata validation
    # ---------------------------------------------

    assert result.project_name == (
        "Delhi Metro Extension"
    )

    assert result.report_date == (
        "5 June 2025"
    )

    assert result.location == "Block A"

    # ---------------------------------------------
    # Activity validation
    # ---------------------------------------------

    assert len(result.activities) == 1

    activity = result.activities[0]

    assert activity.activity_name == (
        "Foundation RCC work"
    )

    assert activity.quantity_completed == 120

    assert activity.unit in {
        "cubic meters",
        "m3",
    }

    assert activity.progress_percentage == 70

    assert activity.status == "In Progress"

    # ---------------------------------------------
    # Issue / delay validation
    # ---------------------------------------------

    assert "Heavy rainfall" in activity.issues

    assert activity.delay_reason == (
        "Heavy rainfall"
    )

    assert activity.delay_duration_hours == 3