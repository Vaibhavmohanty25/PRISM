from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.agents.groq_adapter import GroqLLMAdapter


def test_groq_adapter_converts_prism_tool_schema():
    client = Mock()

    adapter = GroqLLMAdapter(
        client=client,
        model="test-model",
    )

    tools = [
        {
            "name": "get_project_predictive_summary",
            "description": "Get project summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                    }
                },
                "required": [
                    "project_name",
                ],
            },
        }
    ]

    result = adapter.build_groq_tools(
        tools
    )

    assert result == [
        {
            "type": "function",
            "function": {
                "name": "get_project_predictive_summary",
                "description": "Get project summary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                        }
                    },
                    "required": [
                        "project_name",
                    ],
                },
            },
        }
    ]


def test_groq_adapter_parses_tool_call():
    client = Mock()

    adapter = GroqLLMAdapter(
        client=client,
        model="test-model",
    )

    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                name="get_activity_history",
                                arguments=(
                                    '{"project_name":"Project Alpha",'
                                    '"activity_name":"Foundation Work"}'
                                ),
                            )
                        )
                    ],
                )
            )
        ]
    )

    result = adapter.parse_completion(
        completion
    )

    assert result == {
        "type": "tool_call",
        "tool_name": "get_activity_history",
        "arguments": {
            "project_name": "Project Alpha",
            "activity_name": "Foundation Work",
        },
    }


def test_groq_adapter_parses_final_answer():
    client = Mock()

    adapter = GroqLLMAdapter(
        client=client,
        model="test-model",
    )

    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="PRISM grounded answer.",
                    tool_calls=None,
                )
            )
        ]
    )

    result = adapter.parse_completion(
        completion
    )

    assert result == {
        "type": "final",
        "answer": "PRISM grounded answer.",
    }


def test_groq_adapter_calls_chat_completions():
    client = Mock()

    client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Final answer.",
                        tool_calls=None,
                    )
                )
            ]
        )
    )

    adapter = GroqLLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.respond(
        messages=[
            {
                "role": "user",
                "content": "Analyze Project Alpha.",
            }
        ],
        tools=[],
    )

    assert result["type"] == "final"

    client.chat.completions.create.assert_called_once()


def test_groq_adapter_omits_tool_fields_when_no_tools():
    client = Mock()

    client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="PRISM GROQ OK",
                        tool_calls=None,
                    )
                )
            ]
        )
    )

    adapter = GroqLLMAdapter(
        client=client,
        model="test-model",
    )

    adapter.respond(
        messages=[
            {
                "role": "user",
                "content": "Run smoke test.",
            }
        ],
        tools=[],
    )

    kwargs = (
        client.chat.completions.create.call_args.kwargs
    )

    assert "tools" not in kwargs
    assert "tool_choice" not in kwargs