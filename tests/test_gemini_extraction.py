from unittest.mock import MagicMock, patch

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

    # --------------------------------------------------------
    # Mock Gemini API response
    # --------------------------------------------------------

    mock_interaction = MagicMock()

    mock_interaction.output_text = """
    {
        "activities": [
            {
                "activity_name": "Foundation RCC work",
                "quantity_completed": 120,
                "unit": "cubic meters",
                "progress_percentage": 70,
                "status": "In Progress",
                "issues": [
                    "Heavy rainfall"
                ],
                "delay_reason": "Heavy rainfall",
                "delay_duration_hours": 3
            }
        ],
        "general_issues": []
    }
    """

    with patch.object(
        service.client.interactions,
        "create",
        return_value=mock_interaction,
    ) as mock_create:

        result = service.extract_progress_report(
            source_text
        )

    # --------------------------------------------------------
    # Verify Gemini was called
    # --------------------------------------------------------

    mock_create.assert_called_once()

    # --------------------------------------------------------
    # Metadata validation
    # --------------------------------------------------------

    assert result.project_name == (
        "Delhi Metro Extension"
    )

    assert result.report_date == (
        "5 June 2025"
    )

    assert result.location == "Block A"

    # --------------------------------------------------------
    # Activity validation
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Issue / delay validation
    # --------------------------------------------------------

    assert "Heavy rainfall" in activity.issues

    assert activity.delay_reason == (
        "Heavy rainfall"
    )

    assert activity.delay_duration_hours == 3