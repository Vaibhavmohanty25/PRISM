from types import SimpleNamespace
from unittest.mock import Mock

from app.agents.agent import ConstructionIntelligenceAgent
from app.agents.groq_adapter import GroqLLMAdapter
from app.agents.tool_registry import ToolRegistry
from app.agents.tools import PrismAgentTools
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService


def build_agent_with_mocked_groq():
    analysis_service = AnalysisService()

    tools = PrismAgentTools(
        analysis_service
    )

    registry = ToolRegistry(
        tools
    )

    client = Mock()

    adapter = GroqLLMAdapter(
        client=client,
        model="test-model",
    )

    agent = ConstructionIntelligenceAgent(
        llm=adapter,
        registry=registry,
    )

    return (
        analysis_service,
        client,
        agent,
    )


def make_groq_tool_call(
    tool_name: str,
    arguments: str,
):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                name=tool_name,
                                arguments=arguments,
                            )
                        )
                    ],
                )
            )
        ]
    )


def make_groq_final_answer(
    answer: str,
):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=answer,
                    tool_calls=None,
                )
            )
        ]
    )


def test_agent_executes_real_project_tool_with_mocked_groq():
    (
        analysis_service,
        client,
        agent,
    ) = build_agent_with_mocked_groq()

    report = ProgressReport(
        project_name="Project Alpha",
        report_date="2026-09-01",
        activities=[
            ActivityProgress(
                activity_name="Foundation Work",
                progress_percentage=25,
            )
        ],
    )

    analysis_service.record_report(
        report
    )

    client.chat.completions.create.side_effect = [
        make_groq_tool_call(
            "get_project_predictive_summary",
            '{"project_name":"Project Alpha"}',
        ),
        make_groq_final_answer(
            "Project Alpha has one recorded activity. "
            "The available evidence is limited."
        ),
    ]

    result = agent.run(
        "Give me the predictive status of Project Alpha."
    )

    assert result["answer"] == (
        "Project Alpha has one recorded activity. "
        "The available evidence is limited."
    )

    assert result["tools_used"] == [
        "get_project_predictive_summary"
    ]

    assert result["iterations"] == 2

    assert client.chat.completions.create.call_count == 2


def test_agent_executes_real_activity_tool_with_mocked_groq():
    (
        analysis_service,
        client,
        agent,
    ) = build_agent_with_mocked_groq()

    first_report = ProgressReport(
        project_name="Project Alpha",
        report_date="2026-09-01",
        activities=[
            ActivityProgress(
                activity_name="Foundation Work",
                progress_percentage=20,
            )
        ],
    )

    second_report = ProgressReport(
        project_name="Project Alpha",
        report_date="2026-09-11",
        activities=[
            ActivityProgress(
                activity_name="Foundation Work",
                progress_percentage=40,
            )
        ],
    )

    analysis_service.record_report(
        first_report
    )

    analysis_service.record_report(
        second_report
    )

    client.chat.completions.create.side_effect = [
        make_groq_tool_call(
            "get_activity_predictive_summary",
            (
                '{"project_name":"Project Alpha",'
                '"activity_name":"Foundation Work"}'
            ),
        ),
        make_groq_final_answer(
            "Foundation Work has a PRISM predictive summary."
        ),
    ]

    result = agent.run(
        "When is Foundation Work expected to finish?"
    )

    assert result["answer"] == (
        "Foundation Work has a PRISM predictive summary."
    )

    assert result["tools_used"] == [
        "get_activity_predictive_summary"
    ]

    assert result["iterations"] == 2

    assert client.chat.completions.create.call_count == 2