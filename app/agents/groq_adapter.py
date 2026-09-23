import json
from typing import Any

from app.agents.llm_adapter import (
    AgentLLMError,
    AgentRateLimitError,
    AgentServiceUnavailableError,
)


class GroqLLMAdapter:
    """
    Adapter between PRISM's provider-neutral agent interface
    and Groq's Chat Completions API.
    """

    def __init__(
        self,
        client: Any,
        model: str,
    ):
        self.client = client
        self.model = model

    @staticmethod
    def build_groq_tools(
        tools: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        groq_tools = []

        for tool in tools:
            groq_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
            )

        return groq_tools

    @staticmethod
    def build_messages(
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        groq_messages = []

        for message in messages:
            role = message.get("role")

            if role in {"system", "user"}:
                groq_messages.append(
                    {
                        "role": role,
                        "content": message.get("content", ""),
                    }
                )

            elif role == "assistant" and "tool_call" in message:
                tool_call = message["tool_call"]

                groq_messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "Requested PRISM tool "
                            f"{tool_call.get('name')}."
                        ),
                    }
                )

            elif role == "tool":
                groq_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "PRISM TOOL OBSERVATION\n"
                            f"Tool: {message.get('name')}\n"
                            f"Result: "
                            f"{json.dumps(message.get('content'), default=str)}"
                        ),
                    }
                )

        return groq_messages

    @staticmethod
    def parse_completion(
        completion: Any,
    ) -> dict[str, Any]:
        choices = getattr(
            completion,
            "choices",
            None,
        )

        if not choices:
            raise ValueError(
                "Groq returned no usable response."
            )

        message = choices[0].message

        tool_calls = getattr(
            message,
            "tool_calls",
            None,
        )

        if tool_calls:
            tool_call = tool_calls[0]

            function = getattr(
                tool_call,
                "function",
                None,
            )

            if function is None:
                raise ValueError(
                    "Groq returned an invalid tool call."
                )

            tool_name = getattr(
                function,
                "name",
                None,
            )

            raw_arguments = getattr(
                function,
                "arguments",
                "{}",
            )

            if not isinstance(tool_name, str):
                raise ValueError(
                    "Groq returned an invalid function name."
                )

            try:
                arguments = json.loads(
                    raw_arguments
                )
            except (
                TypeError,
                json.JSONDecodeError,
            ) as exc:
                raise ValueError(
                    "Groq returned invalid function arguments."
                ) from exc

            if not isinstance(arguments, dict):
                raise ValueError(
                    "Groq returned invalid function arguments."
                )

            return {
                "type": "tool_call",
                "tool_name": tool_name,
                "arguments": arguments,
            }

        content = getattr(
            message,
            "content",
            None,
        )

        if isinstance(content, str) and content.strip():
            return {
                "type": "final",
                "answer": content.strip(),
            }

        raise ValueError(
            "Groq returned no usable response."
        )

    def respond(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        groq_tools = self.build_groq_tools(
            tools
        )

        groq_messages = self.build_messages(
            messages
        )

        request_kwargs = {
            "model": self.model,
            "messages": groq_messages,
        }

        if groq_tools:
            request_kwargs["tools"] = groq_tools
            request_kwargs["tool_choice"] = "auto"

        try:
            completion = self.client.chat.completions.create(
                **request_kwargs
            )

        except Exception as exc:
            message = str(exc).lower()
            exception_name = type(exc).__name__.lower()

            if (
                "429" in message
                or "rate limit" in message
                or "ratelimit" in exception_name
            ):
                raise AgentRateLimitError(
                    "The AI service rate limit has been reached. "
                    "Please try again later."
                ) from exc

            if (
                "503" in message
                or "service unavailable" in message
                or "serviceunavailable" in exception_name
            ):
                raise AgentServiceUnavailableError(
                    "The AI service is temporarily unavailable. "
                    "Please try again later."
                ) from exc

            raise AgentLLMError(
                "The AI service request failed."
            ) from exc

        return self.parse_completion(
            completion
        )