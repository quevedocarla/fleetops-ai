import json

from ollama import chat

from app.core.database import SessionLocal
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

    print("\n3 - Enviando evidencias ao LLM...")

    response = chat(
        model="qwen2.5:1.5b-instruct",
        messages=[
            {
                "role": "system",
                "content": (
                    "Voce e um assistente de diagnostico operacional. "
                    "OS significa Ordem de Servico. "
                    "Use SOMENTE os dados fornecidos pelo sistema. "
                    "Nao invente fatos. "
                    "Nao generalize alem das evidencias. "
                    "Se o contrato informado estiver INACTIVE, diga apenas "
                    "que aquele contrato esta inativo. "
                    "Responda em portugues, de forma curta e objetiva."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Explique o motivo do diagnostico abaixo para um usuario "
                    "nao tecnico.\n\n"
                    "DADOS DO SISTEMA:\n"
                    + json.dumps(
                        diagnostic,
                        ensure_ascii=False,
                        default=str,
                    )
                ),
            },
        ],
    )

    print("\n4 - Resposta do LLM:")
    print(response.message.content)

finally:
    db.close()