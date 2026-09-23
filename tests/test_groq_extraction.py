import json
from types import SimpleNamespace
from unittest.mock import patch

from app.core.config import settings
from app.services.extraction_service import ExtractionService
from app.services.analysis_service import AnalysisService


def _completion(payload: dict):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(payload)
                )
            )
        ]
    )


def test_gemini_extraction():
    service = ExtractionService(
        settings.GROQ_API_KEY,
        model=settings.GROQ_EXTRACTION_MODEL,
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

    mock_completion = _completion(
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
                    "delay_duration_hours": 3,
                }
            ],
            "general_issues": [],
        }
    )

    with patch.object(
        service.client.chat.completions,
        "create",
        return_value=mock_completion,
    ) as mock_create:
        result = service.extract_progress_report(
            source_text
        )

    mock_create.assert_called_once()

    assert result.project_name == (
        "Delhi Metro Extension"
    )

    assert result.report_date == (
        "5 June 2025"
    )

    assert result.location == "Block A"

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

    assert "Heavy rainfall" in activity.issues

    assert activity.delay_reason == (
        "Heavy rainfall"
    )

    assert activity.delay_duration_hours == 3


def test_demo_shape_preserves_vertical_metadata_and_activity_evidence():
    service = ExtractionService(
        settings.GROQ_API_KEY,
        model=settings.GROQ_EXTRACTION_MODEL,
    )

    source_text = """
RIVERSIDE COMMERCIAL COMPLEX

Project
Riverside Commercial Complex

Date
14 August 2026

Location
Site A

Activity: Foundation Works
Foundation Works is 72 percent complete.

Activity: Structural Framing
Structural Framing is 55 percent complete.

Activity: Electrical Installation
Electrical Installation is 20 percent complete.

Activity: Plumbing Works
Plumbing Works is 25 percent complete.

Activity: Masonry Works
Masonry Works is 35 percent complete.

Activity: Interior Finishing
Interior Finishing is 0 percent complete.
"""

    activities = [
        {
            "activity_name": "Foundation Works",
            "progress_percentage": 72,
        },
        {
            "activity_name": "Structural Framing",
            "progress_percentage": 55,
            "issues": [
                "Steel delivery was delayed by the supplier"
            ],
            "delay_reason": "Steel delivery delay",
            "delay_duration_hours": 10,
        },
        {
            "activity_name": "Electrical Installation",
            "progress_percentage": 20,
            "issues": [
                "Electrical materials were not fully available"
            ],
            "delay_reason": "Electrical material shortage",
            "delay_duration_hours": 6,
        },
        {
            "activity_name": "Plumbing Works",
            "progress_percentage": 25,
            "delay_duration_hours": 0,
        },
        {
            "activity_name": "Masonry Works",
            "progress_percentage": 35,
            "issues": [
                "Heavy rainfall affected Masonry Works"
            ],
            "delay_reason": "Heavy rainfall",
            "delay_duration_hours": 8,
        },
        {
            "activity_name": "Interior Finishing",
            "progress_percentage": 0,
        },
    ]

    mock_completion = _completion(
        {
            "activities": activities,
            "general_issues": [],
        }
    )

    with patch.object(
        service.client.chat.completions,
        "create",
        return_value=mock_completion,
    ):
        result = service.extract_progress_report(
            source_text
        )

    assert result.project_name == (
        "Riverside Commercial Complex"
    )

    assert result.report_date == (
        "14 August 2026"
    )

    assert result.location == "Site A"

    assert len(result.activities) == 6

    assert [
        activity.progress_percentage
        for activity in result.activities
    ] == [
        72,
        55,
        20,
        25,
        35,
        0,
    ]

    assert (
        result.activities[1].delay_duration_hours
        == 10
    )

    assert (
        result.activities[1].delay_reason
        == "Steel delivery delay"
    )

    assert (
        result.activities[2].delay_duration_hours
        == 6
    )

    assert (
        result.activities[3].delay_duration_hours
        == 0
    )

    assert (
        result.activities[4].delay_duration_hours
        == 8
    )

    assert result.activities[4].issues == [
        "Heavy rainfall affected Masonry Works"
    ]

    analysis_service = AnalysisService()

    analysis_service.record_report(
        result
    )

    snapshot = (
        analysis_service
        .get_activity_history(
            "Riverside Commercial Complex",
            "Masonry Works",
        )
        .snapshots[0]
    )

    assert snapshot.issues == [
        "Heavy rainfall affected Masonry Works"
    ]


def test_complete_activity_response_is_accepted_without_retry():
    service = ExtractionService(
        settings.GROQ_API_KEY,
        model=settings.GROQ_EXTRACTION_MODEL,
    )

    source_text = """
Activity: Excavation
Excavation is 40 percent complete.

Activity: Concrete
Concrete is 20 percent complete.
"""

    response = _completion(
        {
            "activities": [
                {
                    "activity_name": "Excavation",
                    "progress_percentage": 40,
                },
                {
                    "activity_name": "Concrete",
                    "progress_percentage": 20,
                },
            ],
            "general_issues": [],
        }
    )

    with patch.object(
        service.client.chat.completions,
        "create",
        return_value=response,
    ) as create:
        result = service.extract_progress_report(
            source_text
        )

    assert len(result.activities) == 2

    create.assert_called_once()

    assert (
        create.call_args.kwargs["temperature"]
        == 0
    )

    assert (
        create.call_args.kwargs["model"]
        == settings.GROQ_EXTRACTION_MODEL
    )

    assert (
        create.call_args.kwargs[
            "response_format"
        ]["type"]
        == "json_schema"
    )


def test_incomplete_activity_response_retries_and_parses_recovery():
    service = ExtractionService(
        settings.GROQ_API_KEY,
        model=settings.GROQ_EXTRACTION_MODEL,
    )

    source_text = """
Activity: Excavation
Excavation is 40 percent complete.

Activity: Concrete
Concrete is 20 percent complete.

Activity: Steel
Steel is 10 percent complete.
"""

    incomplete = _completion(
        {
            "activities": [
                {
                    "activity_name": "Excavation",
                    "progress_percentage": 40,
                }
            ],
            "general_issues": [],
        }
    )

    recovered = _completion(
        {
            "activities": [
                {
                    "activity_name": "Excavation",
                    "progress_percentage": 40,
                },
                {
                    "activity_name": "Concrete",
                    "progress_percentage": 20,
                },
                {
                    "activity_name": "Steel",
                    "progress_percentage": 10,
                    "issues": [
                        "Steel delivery delay"
                    ],
                    "delay_reason": (
                        "Steel delivery delay"
                    ),
                    "delay_duration_hours": 4,
                },
            ],
            "general_issues": [],
        }
    )

    with patch.object(
        service.client.chat.completions,
        "create",
        side_effect=[
            incomplete,
            recovered,
        ],
    ) as create:
        result = service.extract_progress_report(
            source_text
        )

    assert [
        activity.activity_name
        for activity in result.activities
    ] == [
        "Excavation",
        "Concrete",
        "Steel",
    ]

    assert (
        result.activities[2].delay_duration_hours
        == 4
    )

    assert result.activities[2].issues == [
        "Steel delivery delay"
    ]

    assert create.call_count == 2

    retry_messages = (
        create.call_args_list[1]
        .kwargs["messages"]
    )

    retry_prompt = (
        retry_messages[0]["content"]
        .lower()
    )

    assert (
        "every activity explicitly identified"
        in retry_prompt
    )


def test_sparse_report_does_not_trigger_completeness_retry():
    service = ExtractionService(
        settings.GROQ_API_KEY,
        model=settings.GROQ_EXTRACTION_MODEL,
    )

    source_text = (
        "The report only states that site work is ongoing."
    )

    response = _completion(
        {
            "activities": [],
            "general_issues": [],
        }
    )

    with patch.object(
        service.client.chat.completions,
        "create",
        return_value=response,
    ) as create:
        result = service.extract_progress_report(
            source_text
        )

    assert result.activities == []

    create.assert_called_once()


def test_explicit_evidence_with_null_fields_triggers_recovery():
    service = ExtractionService(
        settings.GROQ_API_KEY,
        model=settings.GROQ_EXTRACTION_MODEL,
    )

    source_text = """
Activity: Foundation Works
Foundation Works is 72 percent complete.

Activity: Structural Works
Structural Works is 55 percent complete.
Structural Works experienced a 10 hour steel delivery delay.
Issue: Steel delivery was delayed by the supplier.
"""

    incomplete = _completion(
        {
            "activities": [
                {
                    "activity_name": "Foundation Works"
                },
                {
                    "activity_name": "Structural Works"
                },
            ],
            "general_issues": [],
        }
    )

    recovered = _completion(
        {
            "activities": [
                {
                    "activity_name": "Foundation Works",
                    "progress_percentage": 72,
                },
                {
                    "activity_name": "Structural Works",
                    "progress_percentage": 55,
                    "delay_duration_hours": 10,
                    "delay_reason": (
                        "Steel delivery delay"
                    ),
                    "issues": [
                        (
                            "Steel delivery was "
                            "delayed by the supplier."
                        )
                    ],
                },
            ],
            "general_issues": [],
        }
    )

    with patch.object(
        service.client.chat.completions,
        "create",
        side_effect=[
            incomplete,
            recovered,
        ],
    ) as create:
        result = service.extract_progress_report(
            source_text
        )

    assert (
        result.activities[0].progress_percentage
        == 72
    )

    assert (
        result.activities[1].progress_percentage
        == 55
    )

    assert (
        result.activities[1].delay_duration_hours
        == 10
    )

    assert (
        result.activities[1].delay_reason
        == "Steel delivery delay"
    )

    assert result.activities[1].issues == [
        (
            "Steel delivery was "
            "delayed by the supplier."
        )
    ]

    assert create.call_count == 2

    retry_messages = (
        create.call_args_list[1]
        .kwargs["messages"]
    )

    retry_prompt = (
        retry_messages[0]["content"]
        .lower()
    )

    assert (
        "map every explicit progress"
        in retry_prompt
    )

    assert "delay" in retry_prompt

    assert "issue" in retry_prompt


def test_sparse_activity_without_evidence_is_accepted():
    service = ExtractionService(
        settings.GROQ_API_KEY,
        model=settings.GROQ_EXTRACTION_MODEL,
    )

    source_text = """
Activity: Excavation

Work is ongoing.
"""

    response = _completion(
        {
            "activities": [
                {
                    "activity_name": "Excavation"
                }
            ],
            "general_issues": [],
        }
    )

    with patch.object(
        service.client.chat.completions,
        "create",
        return_value=response,
    ) as create:
        result = service.extract_progress_report(
            source_text
        )

    assert (
        result.activities[0].activity_name
        == "Excavation"
    )

    assert (
        result.activities[0].progress_percentage
        is None
    )

    create.assert_called_once()