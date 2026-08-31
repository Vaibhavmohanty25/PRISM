from app.schemas.project_data import ProgressReport


# ============================================================
# UNIT NORMALIZATION
# ============================================================

def normalize_unit(
    unit: str | None
) -> str | None:

    if not unit:
        return None

    unit = unit.strip().lower()

    mappings = {
        "cubic meter": "cubic meters",
        "cubic meters": "cubic meters",
        "cubic metre": "cubic meters",
        "cubic metres": "cubic meters",

        "m3": "m3",
        "m^3": "m3",

        "square meter": "square meters",
        "square meters": "square meters",
        "square metre": "square meters",
        "square metres": "square meters",

        "m2": "m2",
        "m^2": "m2",
        "m²": "m²",

        "meter": "meters",
        "meters": "meters",
        "metre": "meters",
        "metres": "meters",

        "kg": "kg",

        "tonne": "tonnes",
        "tonnes": "tonnes",

        "ton": "tons",
        "tons": "tons",

        "unit": "units",
        "units": "units",
    }

    if unit in mappings:
        return mappings[unit]

    # Reject obvious Gemini contamination
    if len(unit) > 30:
        return None

    if len(unit.split()) > 5:
        return None

    return unit


# ============================================================
# DEDUPLICATE ACTIVITIES
# ============================================================

def deduplicate_activities(
    report: ProgressReport
) -> ProgressReport:
    """
    Remove accidental duplicate activities produced by Gemini.

    Activities are considered duplicates only when their names
    are exactly the same after normalization.

    Different activity names are NEVER merged.
    """

    unique_activities = {}

    for activity in report.activities:

        if not activity.activity_name:
            continue

        activity.activity_name = (
            activity.activity_name.strip()
        )

        key = activity.activity_name.lower()

        # First occurrence
        if key not in unique_activities:

            unique_activities[key] = activity

            continue

        # Duplicate occurrence
        existing = unique_activities[key]

        # Fill missing fields only
        if existing.quantity_completed is None:
            existing.quantity_completed = (
                activity.quantity_completed
            )

        if existing.unit is None:
            existing.unit = activity.unit

        if existing.progress_percentage is None:
            existing.progress_percentage = (
                activity.progress_percentage
            )

        if existing.status is None:
            existing.status = activity.status

        if existing.delay_reason is None:
            existing.delay_reason = (
                activity.delay_reason
            )

        if existing.delay_duration_hours is None:
            existing.delay_duration_hours = (
                activity.delay_duration_hours
            )

        # Merge issues
        existing.issues = list(
            dict.fromkeys(
                existing.issues + activity.issues
            )
        )

    report.activities = list(
        unique_activities.values()
    )

    return report


# ============================================================
# VALIDATE PROGRESS REPORT
# ============================================================

def validate_progress_report(
    report: ProgressReport
) -> ProgressReport:
    """
    Validate and normalize Gemini's extracted report.

    This layer does NOT invent missing information.
    """

    for activity in report.activities:

        # ----------------------------------------------------
        # Normalize activity name
        # ----------------------------------------------------

        if activity.activity_name:
            activity.activity_name = (
                activity.activity_name.strip()
            )

        # ----------------------------------------------------
        # Normalize unit
        # ----------------------------------------------------

        activity.unit = normalize_unit(
            activity.unit
        )

        # ----------------------------------------------------
        # Validate progress percentage
        # ----------------------------------------------------

        if activity.progress_percentage is not None:

            if not (
                0 <= activity.progress_percentage <= 100
            ):
                activity.progress_percentage = None

        # ----------------------------------------------------
        # Validate quantity
        # ----------------------------------------------------

        if activity.quantity_completed is not None:

            if activity.quantity_completed < 0:
                activity.quantity_completed = None

        # ----------------------------------------------------
        # Validate delay duration
        # ----------------------------------------------------

        if activity.delay_duration_hours is not None:

            if activity.delay_duration_hours < 0:
                activity.delay_duration_hours = None

    # --------------------------------------------------------
    # Deduplicate only exact activity-name duplicates
    # --------------------------------------------------------

    return deduplicate_activities(report)