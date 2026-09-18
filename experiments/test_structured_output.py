import json

from ollama import chat

from app.core.database import SessionLocal
from app.schemas.ai_diagnostic import AIDiagnosticResponse
from app.services.service_order_service import ServiceOrderService


SERVICE_ORDER_ID = 10235


db = SessionLocal()

try:
    print("1 - Buscando diagnostico no banco...")

    diagnostic = ServiceOrderService.diagnose(
        db,
        SERVICE_ORDER_ID,
    )

    if diagnostic is None:
        raise RuntimeError(
            f"OS {SERVICE_ORDER_ID} nao encontrada."
        )

    print("2 - Diagnostico encontrado:")
    print(
        json.dumps(
            diagnostic,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )

    print("\n3 - Chamando LLM com Structured Output...")

    response = chat(
        model="qwen2.5:3b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Voce e um assistente de diagnostico operacional. "
                    "Use somente os dados fornecidos. "
                    "Nao invente informacoes. "
                    "Nao altere o status calculado pelo sistema. "
                    "OS significa Ordem de Servico."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Explique o diagnostico abaixo.\n\n"
                    + json.dumps(
                        diagnostic,
                        ensure_ascii=False,
                        default=str,
                    )
                ),
            },
        ],
        format=AIDiagnosticResponse.model_json_schema(),
        options={
            "temperature": 0,
        },
    )

    print("\n4 - JSON retornado:")
    print(response.message.content)

    result = AIDiagnosticResponse.model_validate_json(
        response.message.content
    )

    print("\n5 - Validacao Pydantic OK:")
    print(result)

finally:
    db.close()
