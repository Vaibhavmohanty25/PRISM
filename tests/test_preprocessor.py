from app.services.preprocessor import (
    extract_document_metadata,
)


def test_extract_metadata_from_labeled_report():
    text = """
Project: Project Beta
Report Date: 2026-09-20
Location: Ludhiana
Contractor: ABC Construction
"""

    result = extract_document_metadata(
        text
    )

    assert result["project_name"] == "Project Beta"
    assert result["report_date"] == "2026-09-20"
    assert result["location"] == "Ludhiana"
    assert result["contractor"] == "ABC Construction"


def test_extract_metadata_from_prism_sample_report_format():
    text = """
CONSTRUCTION PROGRESS REPORT
Project Alpha

Report Date
2026-09-11

Reporting Period
2026-09-01 to 2026-09-11

Site Location
Jalandhar, Punjab

Prepared By
Site Progress Team
"""

    result = extract_document_metadata(
        text
    )

    assert result["project_name"] == "Project Alpha"
    assert result["report_date"] == "2026-09-11"
    assert result["location"] == "Jalandhar, Punjab"
    assert result["contractor"] is None