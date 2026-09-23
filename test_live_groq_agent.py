from groq import Groq

from app.agents.agent import ConstructionIntelligenceAgent
from app.agents.groq_adapter import GroqLLMAdapter
from app.agents.tool_registry import ToolRegistry
from app.agents.tools import PrismAgentTools
from app.core.config import settings
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService


analysis_service = AnalysisService()

# Seed deterministic PRISM evidence
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

analysis_service.record_report(first_report)
analysis_service.record_report(second_report)

# Build PRISM tool layer
agent_tools = PrismAgentTools(
    analysis_service
)

tool_registry = ToolRegistry(
    agent_tools
)

# Build live Groq adapter
groq_client = Groq(
    api_key=settings.GROQ_API_KEY
)

groq_adapter = GroqLLMAdapter(
    client=groq_client,
    model=settings.GROQ_AGENT_MODEL,
)

# Build full agent
agent = ConstructionIntelligenceAgent(
    llm=groq_adapter,
    registry=tool_registry,
)

result = agent.run(
    "Give me the predictive status of Project Alpha. "
    "Use PRISM evidence and explain what requires attention."
)

print(result)