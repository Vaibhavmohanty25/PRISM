from unittest.mock import Mock

from app.agents.agent import ConstructionIntelligenceAgent


class FakeLLM:
    """
    Deterministic fake LLM used to test the agent loop
    without making any external API calls.
    """

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def respond(self, messages, tools):
        self.calls.append(
            {
                "messages": messages,
                "tools": tools,
            }
        )

        return self.responses.pop(0)


def test_agent_can_return_final_answer_without_tool_call():
    registry = Mock()

    registry.get_tool_schemas.return_value = [
        {
            "name": "get_project_predictive_summary",
            "description": "Get project predictive summary.",
            "parameters": {},
        }
    ]

    llm = FakeLLM(
        responses=[
            {
                "type": "final",
                "answer": "No tool was required.",
            }
        ]
    )

    agent = ConstructionIntelligenceAgent(
        llm=llm,
        registry=registry,
    )

    result = agent.run(
        "What can you help me with?"
    )

    assert result["answer"] == "No tool was required."
    assert result["tools_used"] == []
    assert result["iterations"] == 1

    registry.execute.assert_not_called()


def test_agent_executes_tool_and_returns_final_answer():
    registry = Mock()

    registry.get_tool_schemas.return_value = [
        {
            "name": "get_project_predictive_summary",
            "description": "Get project predictive summary.",
            "parameters": {},
        }
    ]

    registry.execute.return_value = {
        "status": "success",
        "data": {
            "project_name": "Project Alpha",
            "total_activity_count": 3,
        },
    }

    llm = FakeLLM(
        responses=[
            {
                "type": "tool_call",
                "tool_name": "get_project_predictive_summary",
                "arguments": {
                    "project_name": "Project Alpha",
                },
            },
            {
                "type": "final",
                "answer": "Project Alpha contains 3 activities.",
            },
        ]
    )

    agent = ConstructionIntelligenceAgent(
        llm=llm,
        registry=registry,
    )

    result = agent.run(
        "Give me the predictive summary for Project Alpha."
    )

    assert result["answer"] == "Project Alpha contains 3 activities."

    assert result["tools_used"] == [
        "get_project_predictive_summary"
    ]

    assert result["iterations"] == 2

    registry.execute.assert_called_once_with(
        "get_project_predictive_summary",
        {
            "project_name": "Project Alpha",
        },
    )

def test_agent_rejects_unknown_tool_request():
    registry = Mock()

    registry.get_tool_schemas.return_value = []

    registry.execute.side_effect = ValueError(
        "Unknown tool: delete_project"
    )

    llm = FakeLLM(
        responses=[
            {
                "type": "tool_call",
                "tool_name": "delete_project",
                "arguments": {
                    "project_name": "Project Alpha",
                },
            }
        ]
    )

    agent = ConstructionIntelligenceAgent(
        llm=llm,
        registry=registry,
    )

    result = agent.run(
        "Delete Project Alpha."
    )

    assert "Unknown tool" in result["answer"]
    assert result["tools_used"] == []
    assert result["iterations"] == 1


def test_agent_rejects_malformed_llm_response():
    registry = Mock()

    registry.get_tool_schemas.return_value = []

    llm = FakeLLM(
        responses=[
            {
                "unexpected": "value",
            }
        ]
    )

    agent = ConstructionIntelligenceAgent(
        llm=llm,
        registry=registry,
    )

    result = agent.run(
        "Give me project information."
    )

    assert "invalid response" in result["answer"].lower()
    assert result["tools_used"] == []
    assert result["iterations"] == 1


def test_agent_blocks_duplicate_tool_call():
    registry = Mock()

    registry.get_tool_schemas.return_value = []

    registry.execute.return_value = {
        "status": "success",
        "data": {
            "project_name": "Project Alpha",
        },
    }

    repeated_call = {
        "type": "tool_call",
        "tool_name": "get_project_predictive_summary",
        "arguments": {
            "project_name": "Project Alpha",
        },
    }

    llm = FakeLLM(
        responses=[
            repeated_call,
            repeated_call,
        ]
    )

    agent = ConstructionIntelligenceAgent(
        llm=llm,
        registry=registry,
    )

    result = agent.run(
        "Analyze Project Alpha."
    )

    assert "duplicate" in result["answer"].lower()

    assert result["tools_used"] == [
        "get_project_predictive_summary"
    ]

    assert result["iterations"] == 2

    registry.execute.assert_called_once()


def test_agent_stops_at_max_iterations():
    registry = Mock()

    registry.get_tool_schemas.return_value = []

    registry.execute.side_effect = [
        {"status": "success", "data": {"step": 1}},
        {"status": "success", "data": {"step": 2}},
        {"status": "success", "data": {"step": 3}},
    ]

    llm = FakeLLM(
        responses=[
            {
                "type": "tool_call",
                "tool_name": "get_activity_history",
                "arguments": {
                    "project_name": "Project Alpha",
                    "activity_name": "Foundation Work",
                },
            },
            {
                "type": "tool_call",
                "tool_name": "get_activity_predictive_summary",
                "arguments": {
                    "project_name": "Project Alpha",
                    "activity_name": "Foundation Work",
                },
            },
            {
                "type": "tool_call",
                "tool_name": "get_project_predictive_summary",
                "arguments": {
                    "project_name": "Project Alpha",
                },
            },
        ]
    )

    agent = ConstructionIntelligenceAgent(
        llm=llm,
        registry=registry,
        max_iterations=3,
    )

    result = agent.run(
        "Keep investigating Project Alpha."
    )

    assert "allowed number of iterations" in result["answer"]
    assert result["iterations"] == 3
    assert len(result["tools_used"]) == 3

from app.agents.prompts import SYSTEM_PROMPT


def test_agent_includes_system_prompt_in_llm_messages():
    registry = Mock()

    registry.get_tool_schemas.return_value = []

    llm = FakeLLM(
        responses=[
            {
                "type": "final",
                "answer": "Grounded response.",
            }
        ]
    )

    agent = ConstructionIntelligenceAgent(
        llm=llm,
        registry=registry,
    )

    result = agent.run(
        "What is happening with Project Alpha?"
    )

    assert result["answer"] == "Grounded response."

    first_call = llm.calls[0]
    messages = first_call["messages"]

    assert messages[0] == {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }

    assert messages[1] == {
        "role": "user",
        "content": "What is happening with Project Alpha?",
    }