from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):

    thread_id: str = Field(
        min_length=1,
        max_length=100,
    )

    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class AgentChatResponse(BaseModel):

    trace_id: str

    thread_id: str

    service_order_id: int

    status: str | None = None

    answer: str

    degraded: bool = False

    warnings: list[str] = Field(
        default_factory=list
    )

    response_mode: str = "AI"

    sources: list[dict] = Field(
        default_factory=list
    )
