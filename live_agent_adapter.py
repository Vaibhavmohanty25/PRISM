from google import genai

from app.agents.agent import ConstructionIntelligenceAgent
from app.agents.gemini_adapter import GeminiLLMAdapter
from app.agents.tool_registry import ToolRegistry
from app.agents.tools import PrismAgentTools
from app.core.config import settings
from app.schemas.project_data import ActivityProgress, ProgressReport
from app.services.analysis_service import AnalysisService


# ---------------------------------------------------------------------
# Build the real PRISM analytical stack
# ---------------------------------------------------------------------

analysis_service = AnalysisService()

agent_tools = PrismAgentTools(
    analysis_service
)

tool_registry = ToolRegistry(
    agent_tools
)


# ---------------------------------------------------------------------
# Add deterministic project evidence
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Build live Gemini adapter
# ---------------------------------------------------------------------

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)

adapter = GeminiLLMAdapter(
    client=client,
    model=settings.GEMINI_AGENT_MODEL,
)


# ---------------------------------------------------------------------
# Build live agent
# ---------------------------------------------------------------------

agent = ConstructionIntelligenceAgent(
    llm=adapter,
    registry=tool_registry,
)


# ---------------------------------------------------------------------
# Run agent
# ---------------------------------------------------------------------

result = agent.run(
    "Give me the predictive status of Project Alpha. "
    "Use PRISM evidence and explain what requires attention."
)

print(result)