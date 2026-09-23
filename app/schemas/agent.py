from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(
        min_length=1,
        description="Natural-language construction intelligence question.",
    )


class AgentQueryResponse(BaseModel):
    answer: str
    tools_used: list[str]
    iterations: int