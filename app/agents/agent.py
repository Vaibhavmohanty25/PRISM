import json

from app.agents.llm_adapter import AgentLLM
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tool_registry import ToolRegistry


class ConstructionIntelligenceAgent:
    """
    Bounded orchestration layer for PRISM.

    The LLM may decide which approved tool to request,
    but analytical truth remains owned by PRISM's
    deterministic services.
    """

    def __init__(
    self,
    llm: AgentLLM,
    registry: ToolRegistry,
    max_iterations: int = 6,
    ):
        self.llm = llm
        self.registry = registry
        self.max_iterations = max_iterations

    def run(self, query: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": query,
            },
        ]

        tools_used = []
        seen_tool_calls = set()

        tool_schemas = self.registry.get_tool_schemas()

        for iteration in range(1, self.max_iterations + 1):
            response = self.llm.respond(
                messages=messages,
                tools=tool_schemas,
            )

            if not isinstance(response, dict):
                return {
                    "answer": (
                        "The agent received an invalid response "
                        "from the language model."
                    ),
                    "tools_used": tools_used,
                    "iterations": iteration,
                }

            response_type = response.get("type")

            if response_type == "final":
                answer = response.get("answer")

                if not isinstance(answer, str):
                    return {
                        "answer": (
                            "The agent received an invalid response "
                            "from the language model."
                        ),
                        "tools_used": tools_used,
                        "iterations": iteration,
                    }

                return {
                    "answer": answer,
                    "tools_used": tools_used,
                    "iterations": iteration,
                }

            if response_type == "tool_call":
                tool_name = response.get("tool_name")
                arguments = response.get("arguments", {})

                if not isinstance(tool_name, str):
                    return {
                        "answer": (
                            "The agent received an invalid tool request."
                        ),
                        "tools_used": tools_used,
                        "iterations": iteration,
                    }

                if not isinstance(arguments, dict):
                    return {
                        "answer": (
                            "The agent received invalid tool arguments."
                        ),
                        "tools_used": tools_used,
                        "iterations": iteration,
                    }

                call_signature = (
                    tool_name,
                    json.dumps(
                        arguments,
                        sort_keys=True,
                        default=str,
                    ),
                )

                if call_signature in seen_tool_calls:
                    return {
                        "answer": (
                            "The agent stopped because it attempted "
                            "a duplicate tool call."
                        ),
                        "tools_used": tools_used,
                        "iterations": iteration,
                    }

                seen_tool_calls.add(call_signature)

                try:
                    observation = self.registry.execute(
                        tool_name,
                        arguments,
                    )
                except ValueError as exc:
                    return {
                        "answer": str(exc),
                        "tools_used": tools_used,
                        "iterations": iteration,
                    }

                tools_used.append(tool_name)

                messages.append(
                    {
                        "role": "assistant",
                        "tool_call": {
                            "name": tool_name,
                            "arguments": arguments,
                        },
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "name": tool_name,
                        "content": observation,
                    }
                )

                continue

            return {
                "answer": (
                    "The agent received an invalid response "
                    "from the language model."
                ),
                "tools_used": tools_used,
                "iterations": iteration,
            }

        return {
            "answer": (
                "The agent could not complete the request "
                "within the allowed number of iterations."
            ),
            "tools_used": tools_used,
            "iterations": self.max_iterations,
        }