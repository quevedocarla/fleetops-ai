from typing import Literal

from pydantic import BaseModel


class AIDiagnosticResponse(BaseModel):
    service_order_id: int

    status: Literal[
        "OK",
        "WAITING",
        "BLOCKED",
        "REVIEW",
    ]

    summary: str

    evidence: list[str]
