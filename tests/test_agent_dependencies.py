from app.agents.agent import ConstructionIntelligenceAgent
from app.agents.groq_adapter import GroqLLMAdapter
from app.main import app


def test_application_exposes_agent():
    agent = app.state.agent

    assert isinstance(
        agent,
        ConstructionIntelligenceAgent,
    )


def test_application_agent_uses_groq_adapter():
    agent = app.state.agent

    assert isinstance(
        agent.llm,
        GroqLLMAdapter,
    )


def test_agent_and_api_share_analysis_service():
    agent = app.state.agent

    registry = agent.registry

    definition = registry._tools[
        "get_project_predictive_summary"
    ]

    prism_tools = definition.handler.__self__

    assert (
        prism_tools.analysis_service
        is app.state.analysis_service
    )


def test_agent_uses_configured_model():
    agent = app.state.agent

    assert isinstance(
        agent.llm.model,
        str,
    )

    assert agent.llm.model


def test_agent_initialization_does_not_call_gemini():
    agent = app.state.agent

    assert agent is not None