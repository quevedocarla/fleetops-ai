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


def is_fleetops_scope(
    message: str,
    direct_intent: str | None = None,
) -> bool:
    if direct_intent:
        return True

    if extract_service_order_id(message) is not None:
        return True

    text = normalize_user_message(message)
    return any(term in text for term in DOMAIN_TERMS)
