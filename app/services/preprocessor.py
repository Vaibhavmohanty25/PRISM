import re
from typing import Optional


def extract_labeled_value(
    text: str,
    label: str
) -> Optional[str]:

    pattern = rf"(?im)^\s*{re.escape(label)}\s*:\s*(.+?)\s*$"

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(1).strip()

    return None


def extract_document_metadata(
    text: str
) -> dict:

    return {
        "report_date": extract_labeled_value(
            text,
            "Date"
        ),
        "project_name": extract_labeled_value(
            text,
            "Project"
        ),
        "location": extract_labeled_value(
            text,
            "Location"
        ),
    }