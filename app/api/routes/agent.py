import unicodedata

from fastapi import APIRouter, Request

from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
)


router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


def _normalize_agent_text(
    text: str,
) -> str:
    """
    Normalize model-generated typography into
    terminal-safe text.
    """

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    replacements = {
        "\u00a0": " ",
        "\u202f": " ",
        "\u2009": " ",
        "\u2022": "-",   # bullet
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',

        # Common mojibake sequences
        "â¢": "-",
        "â€¢": "-",
        "â¯": " ",
        "â€“": "-",
        "â€”": "-",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
    }

    for original, replacement in replacements.items():
        text = text.replace(
            original,
            replacement,
        )

    return text

@router.post(
    "/query",
    response_model=AgentQueryResponse,
)
def query_agent(
    payload: AgentQueryRequest,
    request: Request,
) -> AgentQueryResponse:
    agent = request.app.state.agent

    result = agent.run(
        payload.query
    )

    return AgentQueryResponse(
        answer=_normalize_agent_text(
            result["answer"]
        ),
        tools_used=result["tools_used"],
        iterations=result["iterations"],
    )