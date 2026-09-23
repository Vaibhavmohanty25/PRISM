from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from app.agents.tools import PrismAgentTools


class ProjectToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str


class ActivityToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str
    activity_name: str


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        arguments_model: type[BaseModel],
        handler: Callable[..., dict],
    ):
        self.name = name
        self.description = description
        self.arguments_model = arguments_model
        self.handler = handler


class ToolRegistry:
    """
    Allow-listed registry of tools available to the PRISM agent.

    The registry validates tool names and arguments before
    invoking any application functionality.
    """

    def __init__(self, tools: PrismAgentTools):
        self._tools = {
            "get_project_predictive_summary": ToolDefinition(
                name="get_project_predictive_summary",
                description=(
                    "Get the predictive summary for a construction project, "
                    "including activity attention requirements, predictive "
                    "risk distribution, forecast status, decision support, "
                    "and evidence limitations."
                ),
                arguments_model=ProjectToolArguments,
                handler=tools.get_project_predictive_summary,
            ),
            "get_activity_predictive_summary": ToolDefinition(
                name="get_activity_predictive_summary",
                description=(
                    "Get the predictive summary for one activity in a project, "
                    "including forecast, confidence, predictive risk, and "
                    "decision support."
                ),
                arguments_model=ActivityToolArguments,
                handler=tools.get_activity_predictive_summary,
            ),
            "get_activity_history": ToolDefinition(
                name="get_activity_history",
                description=(
                    "Get the historical progress observations recorded for "
                    "one activity in a project."
                ),
                arguments_model=ActivityToolArguments,
                handler=tools.get_activity_history,
            ),
        }

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def get_tool_schemas(self) -> list[dict]:
        schemas = []

        for definition in self._tools.values():
            schemas.append(
                {
                    "name": definition.name,
                    "description": definition.description,
                    "parameters": definition.arguments_model.model_json_schema(),
                }
            )

        return schemas

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict:
        definition = self._tools.get(tool_name)

        if definition is None:
            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        try:
            validated = definition.arguments_model.model_validate(
                arguments
            )
        except ValidationError as exc:
            raise ValueError(
                f"Invalid arguments for tool '{tool_name}'"
            ) from exc

        return definition.handler(
            **validated.model_dump()
        )