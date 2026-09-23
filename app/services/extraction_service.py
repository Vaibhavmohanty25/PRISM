import json
import re

from groq import Groq

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

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
    ):
        self.client = Groq(
            api_key=api_key
        )

        self.model = model

    @staticmethod
    def _explicit_activity_names(
        raw_content: str,
    ) -> list[str]:
        names = re.findall(
            r"(?im)^\s*Activity\s*:\s*(.+?)\s*$",
            raw_content,
        )

        return list(
            dict.fromkeys(
                name.strip().casefold()
                for name in names
                if name.strip()
            )
        )

    @staticmethod
    def _explicit_activity_evidence(
        raw_content: str,
    ) -> dict[str, dict[str, bool]]:
        matches = list(
            re.finditer(
                r"(?im)^\s*Activity\s*:\s*(.+?)\s*$",
                raw_content,
            )
        )

        evidence = {}

        for index, match in enumerate(matches):
            block_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(raw_content)
            )

            block = raw_content[
                match.end():block_end
            ]

            delay_hours = re.search(
                r"(?i)\b(\d+(?:\.\d+)?)\s*hours?\b",
                block,
            )

            positive_delay = bool(
                delay_hours
                and float(
                    delay_hours.group(1)
                ) > 0
            )

            evidence[
                match.group(1).strip().casefold()
            ] = {
                "progress": bool(
                    re.search(
                        (
                            r"(?i)\b"
                            r"\d+(?:\.\d+)?"
                            r"\s*(?:%|percent)\b"
                        ),
                        block,
                    )
                ),
                "delay_duration": (
                    bool(
                        re.search(
                            r"(?i)\b(?:delay|delayed)\b",
                            block,
                        )
                    )
                    and delay_hours is not None
                ),
                "delay_reason": positive_delay,
                "issues": bool(
                    re.search(
                        r"(?im)^\s*Issue\s*:",
                        block,
                    )
                ),
            }

        return evidence

    @classmethod
    def _response_is_incomplete(
        cls,
        raw_content: str,
        ai_result: AIActivityExtraction,
    ) -> bool:
        expected_names = (
            cls._explicit_activity_names(
                raw_content
            )
        )

        if not expected_names:
            return False

        actual_names = {
            activity.activity_name.strip().casefold()
            for activity in ai_result.activities
            if activity.activity_name.strip()
        }

        if any(
            expected_name not in actual_names
            for expected_name in expected_names
        ):
            return True

        actual_by_name = {
            activity.activity_name.strip().casefold():
            activity
            for activity in ai_result.activities
        }

        expected_evidence_map = (
            cls._explicit_activity_evidence(
                raw_content
            )
        )

        for (
            name,
            expected_evidence,
        ) in expected_evidence_map.items():
            activity = actual_by_name.get(
                name
            )

            if activity is None:
                return True

            if (
                expected_evidence["progress"]
                and activity.progress_percentage
                is None
            ):
                return True

            if (
                expected_evidence[
                    "delay_duration"
                ]
                and activity.delay_duration_hours
                is None
            ):
                return True

            if (
                expected_evidence[
                    "delay_reason"
                ]
                and activity.delay_reason
                is None
            ):
                return True

            if (
                expected_evidence["issues"]
                and not activity.issues
            ):
                return True

        return False

    @staticmethod
    def _make_groq_strict_schema(
        schema: dict,
    ) -> dict:
        """
        Convert a Pydantic-generated JSON schema
        into a schema compatible with Groq strict
        structured outputs.

        Groq strict mode requires:
        - additionalProperties=False on every object
        - every property listed in required
        """

        normalized_schema = json.loads(
            json.dumps(schema)
        )

        def normalize(node):
            if isinstance(node, dict):
                if node.get("type") == "object":
                    properties = node.get(
                        "properties",
                        {},
                    )

                    node[
                        "additionalProperties"
                    ] = False

                    if properties:
                        node["required"] = list(
                            properties.keys()
                        )

                for value in node.values():
                    normalize(value)

            elif isinstance(node, list):
                for item in node:
                    normalize(item)

        normalize(
            normalized_schema
        )

        return normalized_schema

    def _call_groq(
        self,
        prompt: str,
    ) -> AIActivityExtraction:
        """
        Send the extraction prompt to Groq and
        validate the structured JSON response.
        """

        schema = (
            self._make_groq_strict_schema(
                AIActivityExtraction
                .model_json_schema()
            )
        )

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": (
                    "prism_activity_extraction"
                ),
                "strict": True,
                "schema": schema,
            },
        }

        completion = (
            self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                response_format=response_format,
                temperature=0,
            )
        )

        if not completion.choices:
            raise ValueError(
                "Groq returned no completion"
            )

        content = (
            completion
            .choices[0]
            .message
            .content
        )

        if not content:
            raise ValueError(
                "Groq returned an empty response"
            )

        try:
            parsed = json.loads(
                content
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Groq returned invalid JSON"
            ) from exc

        return (
            AIActivityExtraction
            .model_validate(
                parsed
            )
        )

    def extract_progress_report(
        self,
        raw_content: str,
    ) -> ProgressReport:

        # ------------------------------------------------
        # STEP 1:
        # Deterministic metadata extraction
        # ------------------------------------------------

        metadata = extract_document_metadata(
            raw_content
        )

        # ------------------------------------------------
        # STEP 2:
        # Groq semantic extraction
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

The correct result MUST contain exactly TWO objects.

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
-> progress_percentage = 70

"70% complete."
-> progress_percentage = 70

"60 percent completion."
-> progress_percentage = 60

If no explicit progress percentage exists:

-> progress_percentage = null


========================================================
CURRENT VS PREVIOUS PROGRESS RULE
========================================================

A construction report may include both previous
and current progress.

If the source explicitly labels values as
Previous Progress and Current Progress:

- use Current Progress as progress_percentage
- do NOT use Previous Progress as the current value

Example:

Activity: Foundation Work
Previous Progress: 20%
Current Progress: 40%

Return:

progress_percentage = 40

If a table contains:

Activity
Previous Progress
Current Progress
Status

Foundation Work
20%
40%
In Progress

Then:

activity_name = "Foundation Work"
progress_percentage = 40
status = "In Progress"


========================================================
STATUS RULE
========================================================

Set status to "In Progress" ONLY when the source
explicitly states that the activity is in progress.

Examples:

"in progress"
"currently in progress"
"remains in progress"

-> status = "In Progress"

If the source does not explicitly state the status:

-> status = null

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

Structural steel installation reached
60 percent completion.

45 tonnes of steel were installed.

Work was delayed by 5 hours because of
equipment failure.

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

13. For each activity, map every explicit progress,
    delay, status, and issue statement into the
    corresponding fields.

14. When both previous and current progress appear,
    use the explicitly identified current progress.


========================================================
SOURCE DOCUMENT
========================================================

--- SOURCE START ---

{raw_content}

--- SOURCE END ---
"""

        # ------------------------------------------------
        # STEP 3:
        # Call Groq
        # ------------------------------------------------

        ai_result = self._call_groq(
            prompt
        )

        # ------------------------------------------------
        # STEP 4:
        # Validate response completeness
        # ------------------------------------------------

        if self._response_is_incomplete(
            raw_content,
            ai_result,
        ):
            retry_prompt = f"""
The previous extraction was incomplete.

Re-read the SOURCE DOCUMENT and return one object
for EVERY activity explicitly identified in the
source.

Do not omit activities even when their fields are
null.

Map every explicit progress, delay, status, and
issue statement from each activity.

When both previous and current progress values are
present, use the explicitly identified CURRENT
progress value.

Preserve all activity-specific evidence.

Use null or [] only when evidence is absent.

Return only JSON matching the requested schema.


{prompt}
"""

            ai_result = self._call_groq(
                retry_prompt
            )

            if self._response_is_incomplete(
                raw_content,
                ai_result,
            ):
                raise ValueError(
                    (
                        "Groq returned an incomplete "
                        "activity extraction"
                    )
                )

        # ------------------------------------------------
        # STEP 5:
        # Build final ProgressReport
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
            general_issues=(
                ai_result.general_issues
            ),
            extraction_metadata={
                "source_type": "document",
                "processing_method": (
                    "groq_structured_extraction"
                ),
                "confidence_score": None,
            },
        )

        # ------------------------------------------------
        # STEP 6:
        # Validate and normalize
        # ------------------------------------------------

        return validate_progress_report(
            report
        )