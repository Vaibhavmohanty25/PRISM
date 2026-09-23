from typing import Any

from app.agents.llm_adapter import AgentLLM


class ExampleLLM:
    def respond(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "type": "final",
            "answer": "Example response",
        }


def accepts_agent_llm(llm: AgentLLM) -> AgentLLM:
    return llm


def test_llm_adapter_contract_supports_agent_implementation():
    llm = ExampleLLM()

    result = accepts_agent_llm(llm).respond(
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
        tools=[],
    )

    assert result == {
        "type": "final",
        "answer": "Example response",
    }