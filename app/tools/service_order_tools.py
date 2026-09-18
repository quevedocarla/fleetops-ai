import json

from app.core.database import SessionLocal
from app.services.service_order_service import ServiceOrderService


def get_service_order_diagnostic(
    service_order_id: int,
) -> str:
    """
    Busca o diagnostico operacional de uma Ordem de Servico.

    Args:
        service_order_id:
            Numero da Ordem de Servico que deve ser analisada.

    Returns:
        Diagnostico da Ordem de Servico em formato JSON.
    """

    db = SessionLocal()

    try:
        diagnostic = ServiceOrderService.diagnose(
            db,
            service_order_id,
        )

        if diagnostic is None:
            return json.dumps(
                {
                    "error": "SERVICE_ORDER_NOT_FOUND",
                    "service_order_id": service_order_id,
                }
            )

        return json.dumps(
            diagnostic,
            ensure_ascii=False,
            default=str,
        )

    finally:
        db.close()