import re
from typing import Optional


def extract_labeled_value(
    text: str,
    label: str,
) -> Optional[str]:
    """
    Extract a value from either:

    Label: Value

    or:

    Label
    Value
    """

    pattern = rf"(?im)^\s*{re.escape(label)}\s*:\s*(.+?)\s*$"

    match = re.search(
        pattern,
        text,
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


def extract_project_name(
    text: str,
) -> Optional[str]:
    """
    Extract the project name from common report formats.
    """

    # ---------------------------------------------------------
    # Format 1:
    #
    # Project: Project Alpha
    #
    # Format 2:
    #
    # Project
    # Project Alpha
    # ---------------------------------------------------------

    project_name = extract_labeled_value(
        text,
        "Project",
    )

    if project_name:
        return project_name

    # ---------------------------------------------------------
    # Format 3:
    #
    # Project Name: Project Alpha
    #
    # or
    #
    # Project Name
    # Project Alpha
    # ---------------------------------------------------------

    project_name = extract_labeled_value(
        text,
        "Project Name",
    )

    if project_name:
        return project_name

    # ---------------------------------------------------------
    # Format 4:
    #
    # Project Alpha
    #
    # Standalone project heading.
    # ---------------------------------------------------------

    match = re.search(
        r"(?im)^\s*(Project\s+[A-Za-z0-9][^\r\n]*)\s*$",
        text,
    )

    if match:
        value = match.group(1).strip()

        # Avoid accidentally treating the label
        # "Project Name" as the project itself.
        if value.casefold() != "project name":
            return value

    return None


def extract_location(
    text: str,
) -> Optional[str]:
    """
    Extract location from common construction-report labels.
    """

    return (
        extract_labeled_value(
            text,
            "Location",
        )
        or extract_labeled_value(
            text,
            "Site Location",
        )
        or extract_labeled_value(
            text,
            "Project Location",
        )
    )


def extract_contractor(
    text: str,
) -> Optional[str]:
    """
    Extract contractor when explicitly present.
    """

    return (
        extract_labeled_value(
            text,
            "Contractor",
        )
        or extract_labeled_value(
            text,
            "Main Contractor",
        )
    )


def extract_document_metadata(
    text: str,
) -> dict:
    """
    Deterministically extract document-level metadata.
    """

    return {
        "report_date": (
            extract_labeled_value(
                text,
                "Report Date",
            )
            or extract_labeled_value(
                text,
                "Date",
            )
        ),
        "project_name": extract_project_name(
            text,
        ),
        "contractor": extract_contractor(
            text,
        ),
        "location": extract_location(
            text,
        ),
    }