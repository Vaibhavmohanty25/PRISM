from pathlib import Path
from unittest.mock import patch

from app.services.file_router import process_file


TEST_DOCUMENTS_DIR = Path("test_documents")


# ============================================================
# MOCK GEMINI RESPONSES
# ============================================================

def mock_multiple_activities_extraction(content: str) -> dict:

    return {
        "report_date": "6 June 2025",
        "project_name": "Delhi Metro Extension",
        "contractor": None,
        "location": "Block B",
        "activities": [
            {
                "activity_name": "Column reinforcement work",
                "quantity_completed": 80,
                "unit": "kg",
                "progress_percentage": 45,
                "status": None,
                "issues": [],
                "delay_reason": None,
                "delay_duration_hours": None,
            },
            {
                "activity_name": "Brick masonry work",
                "quantity_completed": 250,
                "unit": "square meters",
                "progress_percentage": 30,
                "status": None,
                "issues": [],
                "delay_reason": None,
                "delay_duration_hours": None,
            },
        ],
        "general_issues": [],
        "extraction_metadata": {
            "source_type": "document",
            "processing_method": "gemini_structured_extraction",
            "confidence_score": None,
        },
    }


def mock_missing_information_extraction(content: str) -> dict:

    return {
        "report_date": "7 June 2025",
        "project_name": "Highway Expansion Project",
        "contractor": None,
        "location": "Section C",
        "activities": [
            {
                "activity_name": "Earthwork excavation",
                "quantity_completed": 350,
                "unit": "cubic meters",
                "progress_percentage": None,
                "status": "In Progress",
                "issues": [],
                "delay_reason": None,
                "delay_duration_hours": None,
            }
        ],
        "general_issues": [],
        "extraction_metadata": {
            "source_type": "document",
            "processing_method": "gemini_structured_extraction",
            "confidence_score": None,
        },
    }


def mock_delay_heavy_extraction(content: str) -> dict:

    return {
        "report_date": "8 June 2025",
        "project_name": "Airport Terminal Expansion",
        "contractor": None,
        "location": "Zone 4",
        "activities": [
            {
                "activity_name": "Structural steel installation",
                "quantity_completed": 45,
                "unit": "tonnes",
                "progress_percentage": 60,
                "status": "In Progress",
                "issues": ["equipment failure"],
                "delay_reason": "equipment failure",
                "delay_duration_hours": 5,
            }
        ],
        "general_issues": [],
        "extraction_metadata": {
            "source_type": "document",
            "processing_method": "gemini_structured_extraction",
            "confidence_score": None,
        },
    }


# ============================================================
# TEST 1 — MULTIPLE ACTIVITIES
# ============================================================

@patch(
    "app.services.file_router.run_ai_extraction",
    side_effect=mock_multiple_activities_extraction,
)
def test_multiple_activities_pdf(mock_ai_extraction):

    file_path = (
        TEST_DOCUMENTS_DIR
        / "report_multiple_activities.pdf"
    )

    result = process_file(
        str(file_path)
    )

    extracted = result["extracted_data"]

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    assert extracted["project_name"] == (
        "Delhi Metro Extension"
    )

    assert extracted["report_date"] == (
        "6 June 2025"
    )

    assert extracted["location"] == "Block B"

    # --------------------------------------------------------
    # Activity count
    # --------------------------------------------------------

    assert len(
        extracted["activities"]
    ) == 2

    # --------------------------------------------------------
    # Activity 1
    # --------------------------------------------------------

    activity_1 = extracted["activities"][0]

    assert activity_1["activity_name"] == (
        "Column reinforcement work"
    )

    assert activity_1["quantity_completed"] == 80

    assert activity_1["unit"] == "kg"

    assert activity_1["progress_percentage"] == 45

    # --------------------------------------------------------
    # Activity 2
    # --------------------------------------------------------

    activity_2 = extracted["activities"][1]

    assert activity_2["activity_name"] == (
        "Brick masonry work"
    )

    assert activity_2["quantity_completed"] == 250

    assert activity_2["unit"] == "square meters"

    assert activity_2["progress_percentage"] == 30

    # --------------------------------------------------------
    # Confirm Gemini was mocked
    # --------------------------------------------------------

    assert mock_ai_extraction.called


# ============================================================
# TEST 2 — MISSING INFORMATION
# ============================================================

@patch(
    "app.services.file_router.run_ai_extraction",
    side_effect=mock_missing_information_extraction,
)
def test_missing_information_pdf(mock_ai_extraction):

    file_path = (
        TEST_DOCUMENTS_DIR
        / "report_missing_information.pdf"
    )

    result = process_file(
        str(file_path)
    )

    extracted = result["extracted_data"]

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    assert extracted["project_name"] == (
        "Highway Expansion Project"
    )

    assert extracted["report_date"] == (
        "7 June 2025"
    )

    assert extracted["location"] == "Section C"

    # --------------------------------------------------------
    # Activity
    # --------------------------------------------------------

    assert len(
        extracted["activities"]
    ) == 1

    activity = extracted["activities"][0]

    assert activity["activity_name"] == (
        "Earthwork excavation"
    )

    assert activity["quantity_completed"] == 350

    assert activity["unit"] == (
        "cubic meters"
    )

    # --------------------------------------------------------
    # Missing information
    # --------------------------------------------------------

    assert (
        activity["progress_percentage"]
        is None
    )

    assert activity["status"] == (
        "In Progress"
    )

    assert activity["delay_reason"] is None

    assert (
        activity["delay_duration_hours"]
        is None
    )

    assert mock_ai_extraction.called


# ============================================================
# TEST 3 — DELAY HEAVY REPORT
# ============================================================

@patch(
    "app.services.file_router.run_ai_extraction",
    side_effect=mock_delay_heavy_extraction,
)
def test_delay_heavy_pdf(mock_ai_extraction):

    file_path = (
        TEST_DOCUMENTS_DIR
        / "report_delay_heavy.pdf"
    )

    result = process_file(
        str(file_path)
    )

    extracted = result["extracted_data"]

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    assert extracted["project_name"] == (
        "Airport Terminal Expansion"
    )

    assert extracted["report_date"] == (
        "8 June 2025"
    )

    assert extracted["location"] == "Zone 4"

    # --------------------------------------------------------
    # Activity
    # --------------------------------------------------------

    assert len(
        extracted["activities"]
    ) == 1

    activity = extracted["activities"][0]

    assert activity["activity_name"] == (
        "Structural steel installation"
    )

    assert activity["quantity_completed"] == 45

    assert activity["unit"] == "tonnes"

    assert activity["progress_percentage"] == 60

    assert activity["status"] == (
        "In Progress"
    )

    # --------------------------------------------------------
    # Delay
    # --------------------------------------------------------

    assert activity["delay_reason"] == (
        "equipment failure"
    )

    assert (
        activity["delay_duration_hours"]
        == 5
    )

    assert "equipment failure" in (
        activity["issues"]
    )

    assert mock_ai_extraction.called