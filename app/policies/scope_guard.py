from app.intents.normalizer import (
    extract_service_order_id,
    normalize_user_message,
)


DOMAIN_TERMS = (
    "ordem de servico",
    "ordem servico",
    "contrato",
    "placa",
    "fila",
    "processamento",
    "bloquead",
    "pendente",
    "instalacao",
    "manutencao",
    "cancelamento",
    "diagnostico",
    "veiculo",
    "servico",
)

CONTEXTUAL_OPERATIONAL_TERMS = (
    "status",
    "situacao",
    "como esta",
    "como ta",
    "em que pe",
    "terminou",
    "concluid",
    "pendente",
    "bloquead",
    "erro",
    "processad",
    "aconteceu",
    "tipo",
)


def is_fleetops_scope(
    message: str,
    direct_intent: str | None = None,
    has_service_order_context: bool = False,
) -> bool:
    if direct_intent:
        return True

    if extract_service_order_id(message) is not None:
        return True

    text = normalize_user_message(message)

    if any(
        term in text
        for term in DOMAIN_TERMS
    ):
        return True

    if (
        has_service_order_context
        and any(
            term in text
            for term in CONTEXTUAL_OPERATIONAL_TERMS
        )
    ):
        return True

    return False
