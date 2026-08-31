from pathlib import Path

from app.services.file_router import process_file


TEST_DOCUMENTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "test_documents"
)


def test_multiple_activities_pdf():

    file_path = (
        TEST_DOCUMENTS_DIR
        / "report_multiple_activities.pdf"
    )

    result = process_file(str(file_path))

    extracted = result["extracted_data"]

    assert extracted["project_name"] == (
        "Delhi Metro Extension"
    )

    assert extracted["report_date"] == (
        "6 June 2025"
    )

    assert extracted["location"] == "Block B"

    assert len(extracted["activities"]) == 2

    activities = extracted["activities"]

    column_work = next(
        activity
        for activity in activities
        if activity["activity_name"]
        == "Column reinforcement work"
    )

    masonry_work = next(
        activity
        for activity in activities
        if activity["activity_name"]
        == "Brick masonry work"
    )

    assert column_work["quantity_completed"] == 80
    assert column_work["unit"] == "kg"
    assert column_work["progress_percentage"] == 45

    assert masonry_work["quantity_completed"] == 250
    assert masonry_work["unit"] == "square meters"
    assert masonry_work["progress_percentage"] == 30


def test_missing_information_pdf():

    file_path = (
        TEST_DOCUMENTS_DIR
        / "report_missing_information.pdf"
    )

    result = process_file(str(file_path))

    extracted = result["extracted_data"]

    assert extracted["project_name"] == (
        "Highway Expansion Project"
    )

    assert extracted["report_date"] == (
        "7 June 2025"
    )

    assert extracted["location"] == "Section C"

    assert len(extracted["activities"]) == 1

    activity = extracted["activities"][0]

    assert activity["activity_name"] == (
        "Earthwork excavation"
    )

    assert activity["quantity_completed"] == 350

    assert activity["unit"] == "cubic meters"

    # Missing information must remain null
    assert activity["progress_percentage"] is None

    assert activity["status"] == "In Progress"

    assert activity["delay_reason"] is None

    assert activity["delay_duration_hours"] is None


def test_delay_heavy_pdf():

    file_path = (
        TEST_DOCUMENTS_DIR
        / "report_delay_heavy.pdf"
    )

    result = process_file(str(file_path))

    extracted = result["extracted_data"]

    assert extracted["project_name"] == (
        "Airport Terminal Expansion"
    )

    assert extracted["report_date"] == (
        "8 June 2025"
    )

    assert extracted["location"] == "Zone 4"

    assert len(extracted["activities"]) == 1

    activity = extracted["activities"][0]

    assert activity["activity_name"] == (
        "Structural steel installation"
    )

    assert activity["quantity_completed"] == 45

    assert activity["unit"] == "tonnes"

    assert activity["progress_percentage"] == 60

    assert activity["status"] == "In Progress"

    assert "equipment failure" in activity["issues"]

    assert activity["delay_reason"] == (
        "equipment failure"
    )

    assert activity["delay_duration_hours"] == 5