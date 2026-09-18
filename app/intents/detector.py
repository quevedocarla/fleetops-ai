import re

from app.intents.models import (
    CONTRACT_NUMBER,
    CONTRACT_STATUS,
    IS_BLOCKED,
    QUEUE_ERROR,
    QUEUE_STATUS,
    SERVICE_ORDER_STATUS,
    SERVICE_ORDER_SUMMARY,
    SERVICE_ORDER_TYPE,
    VEHICLE_PLATE,
    WHY_BLOCKED,
)
from app.intents.normalizer import (
    extract_service_order_id,
    normalize_user_message,
)


SERVICE_TYPE_LABELS = {
    "manutencao": "MAINTENANCE",
    "instalacao": "INSTALLATION",
    "cancelamento": "CANCELLATION",
}


def extract_requested_service_order_type(
    message: str,
) -> str | None:
    text = normalize_user_message(message).strip(" ?.!")

    prefixes = (
        "",
        "e ",
        "esta ",
        "esta em ",
        "ela e ",
        "ela esta ",
        "ela esta em ",
        "a os e ",
        "a os esta ",
        "a os esta em ",
        "a ordem e ",
        "a ordem esta ",
        "a ordem esta em ",
    )

    for label, internal_type in SERVICE_TYPE_LABELS.items():
        if text in {
            f"{prefix}{label}"
            for prefix in prefixes
        }:
            return internal_type

    return None


def detect_direct_intent(
    message: str,
) -> str | None:
    text = normalize_user_message(message)
    stripped = text.strip(" ?.!")
    explicit_os_id = extract_service_order_id(text)

    # =========================================================
    # 1. PREMISSAS SOBRE BLOQUEIO
    # =========================================================
    #
    # "Por que a OS 10236 está bloqueada?"
    # possui uma OS explícita e pode ser validada de forma
    # determinística antes de chegar ao LLM.
    #
    # Já "Por que ela está bloqueada?" é um follow-up
    # contextual/analítico. Mantemos None para preservar
    # o fluxo antigo baseado em memória + análise.
    #
    if "bloquead" in text:
        if any(
            marker in text
            for marker in (
                "por que",
                "porque",
                "qual motivo",
                "motivo",
                "razao",
            )
        ):
            if explicit_os_id is not None:
                return WHY_BLOCKED
            return None

        if any(
            marker in text
            for marker in (
                "esta bloquead",
                "ta bloquead",
                "e bloquead",
            )
        ):
            if explicit_os_id is not None:
                return IS_BLOCKED

    # =========================================================
    # 2. RESUMO / ESTADO GERAL DE OS EXPLÍCITA
    # =========================================================
    if explicit_os_id is not None:
        if re.fullmatch(
            r"(?:a\s+)?"
            r"(?:os|ordem(?:\s+de\s+servico)?)"
            r"\s*[:#-]?\s*\d+",
            stripped,
        ):
            return SERVICE_ORDER_SUMMARY

        if any(
            marker in text
            for marker in (
                "como esta",
                "como ta",
                "como ficou",
                "me fala da",
                "me fale da",
                "resumo",
                "situacao geral",
            )
        ):
            return SERVICE_ORDER_SUMMARY

    # =========================================================
    # 3. CONTRATO
    # =========================================================
    if any(
        pattern in text
        for pattern in (
            "status do contrato",
            "situacao do contrato",
            "contrato esta ativo",
            "contrato esta inativo",
        )
    ):
        return CONTRACT_STATUS

    if (
        stripped
        in {
            "contrato",
            "o contrato",
            "e o contrato",
            "qual contrato",
        }
        or any(
            pattern in stripped
            for pattern in (
                "qual e o contrato",
                "qual o contrato",
                "qual contrato esta vinculado",
                "qual contrato esta associado",
                "contrato vinculado",
                "contrato associado",
                "numero do contrato",
                "contrato dela",
                "contrato dessa os",
                "contrato desta os",
                "contrato dessa ordem",
                "contrato desta ordem",
            )
        )
    ):
        return CONTRACT_NUMBER

    # =========================================================
    # 4. PLACA
    # =========================================================
    plate_text = stripped

    if plate_text.startswith("e "):
        plate_text = plate_text[2:].strip()

    if (
        plate_text in {
            "placa",
            "a placa",
        }
        or any(
            pattern in plate_text
            for pattern in (
                "qual e a placa",
                "qual a placa",
                "placa da os",
                "placa dessa os",
                "placa desta os",
                "placa da ordem",
                "placa dessa ordem",
                "placa desta ordem",
                "placa dela",
                "qual placa",
            )
        )
    ):
        return VEHICLE_PLATE

    # =========================================================
    # 5. TIPO DA OS
    # =========================================================
    if (
        stripped
        in {
            "tipo",
            "o tipo",
        }
        or any(
            pattern in text
            for pattern in (
                "tipo da os",
                "qual e o tipo",
                "qual o tipo",
                "tipo dela",
                "tipo dessa os",
                "tipo desta os",
                "tipo da ordem",
            )
        )
        or extract_requested_service_order_type(message)
        is not None
    ):
        return SERVICE_ORDER_TYPE

    # =========================================================
    # 6. FILA
    # =========================================================
    #
    # IMPORTANTE: fila vem ANTES de status genérico.
    # Caso contrário "status da fila" vira
    # service_order_status.
    #
    if (
        stripped in {
            "fila",
            "a fila",
        }
        or any(
            pattern in text
            for pattern in (
                "status da fila",
                "situacao da fila",
                "como esta a fila",
                "qual e o status da fila",
                "qual o status da fila",
            )
        )
    ):
        return QUEUE_STATUS

    if any(
        pattern in text
        for pattern in (
            "erro da fila",
            "qual e o erro da fila",
            "qual o erro da fila",
            "erro de processamento",
        )
    ):
        return QUEUE_ERROR

    # =========================================================
    # 7. STATUS DA OS
    # =========================================================
    if (
        stripped
        in {
            "status",
            "o status",
            "situacao",
            "a situacao",
        }
        or any(
            pattern in text
            for pattern in (
                "status da os",
                "situacao da os",
                "status da ordem",
                "situacao da ordem",
                "qual e o status",
                "qual o status",
                "esta pendente o status",
                "ta pendente o status",
            )
        )
    ):
        return SERVICE_ORDER_STATUS

    return None
