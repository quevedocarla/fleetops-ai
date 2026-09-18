from app.intents.models import IS_BLOCKED, WHY_BLOCKED


def build_premise_response(
    *,
    intent: str | None,
    diagnostic: dict,
    service_order_id: int,
) -> str | None:
    if intent not in {IS_BLOCKED, WHY_BLOCKED}:
        return None

    diagnostic_status = str(
        diagnostic.get("diagnostic_status") or ""
    ).upper()

    service_order = diagnostic.get("service_order") or {}
    operational_status = str(
        service_order.get("status") or ""
    ).upper()

    if diagnostic_status == "BLOCKED":
        if intent == IS_BLOCKED:
            return f"Sim. A OS {service_order_id} está bloqueada."
        return None

    labels = {
        "COMPLETED": "concluída",
        "PENDING": "pendente",
    }
    status_label = labels.get(
        operational_status,
        operational_status.lower() or "sem status",
    )

    return (
        f"A OS {service_order_id} não está bloqueada. "
        f"Ela está {status_label}."
    )
