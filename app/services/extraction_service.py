from google import genai

from app.schemas.project_data import (
    ProgressReport,
    AIActivityExtraction,
)

from app.services.preprocessor import (
    extract_document_metadata,
)

from app.services.validation_service import (
    validate_progress_report,
)


class ExtractionService:

    def __init__(self, api_key: str):
        self.client = genai.Client(
            api_key=api_key
        )

    def extract_progress_report(
        self,
        raw_content: str
    ) -> ProgressReport:

        # ------------------------------------------------
        # STEP 1: Deterministic metadata extraction
        # ------------------------------------------------

        metadata = extract_document_metadata(
            raw_content
        )

        # ------------------------------------------------
        # STEP 2: Gemini semantic extraction
        # ------------------------------------------------

        prompt = f"""
You are PRISM's construction activity extraction engine.

Your task is to convert the SOURCE DOCUMENT into
structured construction progress data.

The final response MUST contain only valid JSON
matching the provided schema.

Do not provide explanations.
Do not provide commentary.
Do not add fields that are not part of the schema.


========================================================
WHAT YOU MUST EXTRACT
========================================================

Extract ONLY:

- construction activities
- quantity completed
- unit
- progress percentage
- activity status
- activity-specific issues
- delay reason
- delay duration
- general project issues


Do NOT extract or modify:

- project name
- report date
- location
- contractor


========================================================
CORE EXTRACTION RULES
========================================================

1. Extract ONLY information explicitly present
   in the SOURCE DOCUMENT.

2. Never invent information.

3. Never estimate missing information.

4. Never calculate missing information.

5. If a field is not explicitly present, return null.

6. Extract every distinct construction activity.

7. Preserve numeric values from the source.

8. The quantity_completed field MUST contain
   ONLY the numeric quantity.

9. The unit field MUST contain ONLY the unit.

10. Never put explanations inside a field.

11. Never put multiple units inside the unit field.

12. Never repeat an activity unless the source
    clearly describes separate instances.


========================================================
CRITICAL ACTIVITY ASSOCIATION RULE
========================================================

Construction information is often distributed
across multiple consecutive sentences.

You MUST associate each sentence with the activity
it describes.

When several consecutive sentences refer to the
same activity, MERGE them into ONE activity object.

Do NOT treat every sentence as a separate activity.

For example:

Foundation RCC work is 70 percent complete.
120 cubic meters of concrete were completed.
Heavy rainfall delayed the work by 3 hours.
The activity is currently in progress.

These four sentences describe ONE activity.

The correct result is:

{{
    "activity_name": "Foundation RCC work",
    "quantity_completed": 120,
    "unit": "cubic meters",
    "progress_percentage": 70,
    "status": "In Progress",
    "issues": ["Heavy rainfall"],
    "delay_reason": "Heavy rainfall",
    "delay_duration_hours": 3
}}


========================================================
MULTIPLE ACTIVITY RULE
========================================================

If the document introduces a NEW activity, create
a NEW activity object.

Example:

Column reinforcement work is 45 percent complete.
80 kg of reinforcement steel was installed.

Brick masonry work is 30 percent complete.
250 square meters of masonry were completed.

These describe TWO different activities.

The correct result MUST contain exactly TWO objects:

Activity 1:

{{
    "activity_name": "Column reinforcement work",
    "quantity_completed": 80,
    "unit": "kg",
    "progress_percentage": 45,
    "status": null,
    "issues": [],
    "delay_reason": null,
    "delay_duration_hours": null
}}

Activity 2:

{{
    "activity_name": "Brick masonry work",
    "quantity_completed": 250,
    "unit": "square meters",
    "progress_percentage": 30,
    "status": null,
    "issues": [],
    "delay_reason": null,
    "delay_duration_hours": null
}}


IMPORTANT:

Do NOT merge different activities just because
they appear next to each other.

The activity name determines the identity of
the activity.

Different activity names = different activities.


========================================================
DEDUPLICATION RULE
========================================================

Never return duplicate activity objects with the
same activity_name.

If multiple sentences describe the same activity,
merge their information.

For example:

Structural steel installation reached 60 percent
completion.

45 tonnes of steel were installed.

Steel installation remains in progress.

These sentences describe ONE activity:

{{
    "activity_name": "Structural steel installation",
    "quantity_completed": 45,
    "unit": "tonnes",
    "progress_percentage": 60,
    "status": "In Progress",
    "issues": [],
    "delay_reason": null,
    "delay_duration_hours": null
}}

Do NOT create another activity for the
"45 tonnes" sentence.


========================================================
QUANTITY EXTRACTION
========================================================

Extract quantities exactly from the source.

Example:

"120 cubic meters of concrete were completed."

Return:

quantity_completed = 120
unit = "cubic meters"


Example:

"350 cubic meters were excavated."

Return:

quantity_completed = 350
unit = "cubic meters"


Example:

"45 tonnes of steel were installed."

Return:

quantity_completed = 45
unit = "tonnes"


Example:

"80 kg of reinforcement steel was installed."

Return:

quantity_completed = 80
unit = "kg"


========================================================
UNIT RULE
========================================================

The unit field must contain ONLY the unit
associated with the quantity.

Valid examples:

"cubic meters"
"m3"
"kg"
"tonnes"
"square meters"
"m2"

Do NOT:

- add alternative units
- repeat the unit
- add explanations
- add source text
- add calculations
- add unrelated words

For example, this is WRONG:

"cubic meters / m3 / standard unit"

This is CORRECT:

"cubic meters"


========================================================
PROGRESS RULE
========================================================

Extract progress only when explicitly stated.

Examples:

"70 percent complete."
→ progress_percentage = 70

"70% complete."
→ progress_percentage = 70

"60 percent completion."
→ progress_percentage = 60

If no explicit progress percentage exists:

→ progress_percentage = null


========================================================
STATUS RULE
========================================================

Set status to "In Progress" ONLY when the source
explicitly states that the activity is in progress.

Examples:

"in progress"
"currently in progress"
"remains in progress"

→ status = "In Progress"

If the source does not explicitly state the status:

→ status = null

Never infer status from progress percentage.


========================================================
DELAY RULE
========================================================

If the source explicitly mentions a delay, extract
both the reason and duration.

Example:

"Work was delayed by 5 hours because of equipment failure."

Return:

delay_reason = "equipment failure"
delay_duration_hours = 5


Example:

"Heavy rainfall delayed the work by 3 hours."

Return:

delay_reason = "Heavy rainfall"
delay_duration_hours = 3


If no explicit delay exists:

delay_reason = null
delay_duration_hours = null


========================================================
ISSUE RULE
========================================================

Only include explicitly mentioned issues.

Example:

"Heavy rainfall delayed the work by 3 hours."

Return:

issues = ["Heavy rainfall"]

Do NOT invent issues.

Do NOT treat missing information as an issue.


========================================================
GENERAL ISSUE RULE
========================================================

A statement that affects the project generally,
rather than one specific activity, belongs in
general_issues.

Example:

"No major delays were reported."

This is a general project statement.

Do NOT create an activity merely because of this
statement.

If there are no general project issues:

general_issues = []


========================================================
MISSING INFORMATION RULE
========================================================

Never hallucinate missing values.

Example:

Earthwork excavation is currently in progress.
Approximately 350 cubic meters were excavated.

Correct result:

{{
    "activity_name": "Earthwork excavation",
    "quantity_completed": 350,
    "unit": "cubic meters",
    "progress_percentage": null,
    "status": "In Progress",
    "issues": [],
    "delay_reason": null,
    "delay_duration_hours": null
}}

Notice:

progress_percentage = null

because no percentage was explicitly provided.


========================================================
IMPORTANT ASSOCIATION EXAMPLES
========================================================

EXAMPLE 1:

Input:

Column reinforcement work is 45 percent complete.
80 kg of reinforcement steel was installed.

Output:

{{
    "activity_name": "Column reinforcement work",
    "quantity_completed": 80,
    "unit": "kg",
    "progress_percentage": 45,
    "status": null,
    "issues": [],
    "delay_reason": null,
    "delay_duration_hours": null
}}


EXAMPLE 2:

Input:

Brick masonry work is 30 percent complete.
250 square meters of masonry were completed.

Output:

{{
    "activity_name": "Brick masonry work",
    "quantity_completed": 250,
    "unit": "square meters",
    "progress_percentage": 30,
    "status": null,
    "issues": [],
    "delay_reason": null,
    "delay_duration_hours": null
}}


EXAMPLE 3:

Input:

Earthwork excavation is currently in progress.
Approximately 350 cubic meters were excavated.

Output:

{{
    "activity_name": "Earthwork excavation",
    "quantity_completed": 350,
    "unit": "cubic meters",
    "progress_percentage": null,
    "status": "In Progress",
    "issues": [],
    "delay_reason": null,
    "delay_duration_hours": null
}}


EXAMPLE 4:

Input:

Structural steel installation reached 60 percent completion.
45 tonnes of steel were installed.

Work was delayed by 5 hours because of equipment failure.

Steel installation remains in progress.

Output:

{{
    "activity_name": "Structural steel installation",
    "quantity_completed": 45,
    "unit": "tonnes",
    "progress_percentage": 60,
    "status": "In Progress",
    "issues": ["equipment failure"],
    "delay_reason": "equipment failure",
    "delay_duration_hours": 5
}}


========================================================
FINAL CHECK BEFORE RESPONDING
========================================================

Before returning the JSON, verify:

1. Every distinct activity is present.

2. No activity is duplicated.

3. Quantity is numeric only.

4. Unit contains only the unit.

5. Progress is numeric or null.

6. Status is either explicitly extracted or null.

7. Delay reason is explicitly extracted or null.

8. Delay duration is numeric or null.

9. Missing information is represented by null.

10. No hallucinated information exists.

11. The response is valid JSON.

12. The response matches the requested schema.


========================================================
SOURCE DOCUMENT
========================================================

--- SOURCE START ---

{raw_content}

--- SOURCE END ---
"""

        # ------------------------------------------------
        # STEP 3: Call Gemini
        # ------------------------------------------------

        interaction = self.client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": AIActivityExtraction.model_json_schema(),
            },
        )

        # ------------------------------------------------
        # STEP 4: Validate Gemini response
        # ------------------------------------------------

        if not interaction.output_text:
            raise ValueError(
                "Gemini returned an empty response"
            )

        ai_result = (
            AIActivityExtraction.model_validate_json(
                interaction.output_text
            )
        )

        # ------------------------------------------------
        # STEP 5: Build final ProgressReport
        # ------------------------------------------------

        report = ProgressReport(
            report_date=metadata.get(
                "report_date"
            ),
            project_name=metadata.get(
                "project_name"
            ),
            contractor=metadata.get(
                "contractor"
            ),
            location=metadata.get(
                "location"
            ),
            activities=ai_result.activities,
            general_issues=ai_result.general_issues,
            extraction_metadata={
                "source_type": "document",
                "processing_method": (
                    "gemini_structured_extraction"
                ),
                "confidence_score": None,
            },
        )

        # ------------------------------------------------
        # STEP 6: Validate and normalize
        # ------------------------------------------------

        return validate_progress_report(
            report
        )