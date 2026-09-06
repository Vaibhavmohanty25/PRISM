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

    lines = text.splitlines()
    normalized_label = label.strip().casefold()

    for index, line in enumerate(lines):
        if line.strip().casefold() != normalized_label:
            continue

        for following_line in lines[index + 1:]:
            value = following_line.strip()
            if value:
                return value

    return None


def extract_document_metadata(
    text: str
) -> dict:

    return {
        "report_date": extract_labeled_value(
            text,
            "Report Date"
        ) or extract_labeled_value(
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
