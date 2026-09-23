from typing import Any, Protocol


class AgentLLMError(Exception):
    """Base exception for LLM provider failures."""


class AgentRateLimitError(AgentLLMError):
    """Raised when the configured LLM provider rate-limits PRISM."""


class AgentServiceUnavailableError(AgentLLMError):
    """Raised when the configured LLM provider is temporarily unavailable."""


class AgentLLM(Protocol):
    """
    Contract that any LLM adapter used by the PRISM agent must satisfy.
    """

    def respond(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Return either:

        {
            "type": "tool_call",
            "tool_name": "...",
            "arguments": {...},
        }

        or:

        {
            "type": "final",
            "answer": "...",
        }
        """
        ...