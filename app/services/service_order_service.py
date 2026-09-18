from sqlalchemy.orm import Session

from app.repositories.service_order_repository import (
    ServiceOrderRepository,
)


class ServiceOrderService:

    @staticmethod
    def get_service_order(
        db: Session,
        service_order_id: int,
    ):
        order = ServiceOrderRepository.get_service_order(
            db,
            service_order_id,
        )

        if not order:
            return None

        return {
            "id": order.id,
            "contract_id": order.contract_id,
            "vehicle_plate": order.vehicle_plate,
            "type": order.type,
            "status": order.status,
            "created_at": order.created_at,
        }

    @staticmethod
    def diagnose(
        db: Session,
        service_order_id: int,
    ):
        order = ServiceOrderRepository.get_service_order(
            db,
            service_order_id,
        )

        if not order:
            return None

        contract = ServiceOrderRepository.get_contract(
            db,
            order.contract_id,
        )

        queue = ServiceOrderRepository.get_latest_queue(
            db,
            service_order_id,
        )

        problems = []

        if contract is None:
            problems.append(
                "Contrato da OS nao foi encontrado."
            )

        elif contract.status != "ACTIVE":
            problems.append(
                f"Contrato {contract.id} esta inativo."
            )

        if queue is None:
            problems.append(
                "Nao existe fila de processamento para esta OS."
            )

        elif queue.status == "ERROR":
            problems.append(
                f"Fila de processamento esta com erro: {queue.error}"
            )

        if order.status == "COMPLETED":
            diagnostic_status = "OK"

        elif problems:
            diagnostic_status = "BLOCKED"

        elif queue and queue.status == "PENDING":
            diagnostic_status = "WAITING"

        else:
            diagnostic_status = "REVIEW"

        return {
            "service_order": {
                "id": order.id,
                "status": order.status,
                "type": order.type,
                "vehicle_plate": order.vehicle_plate,
            },

            "contract": {
                "id": contract.id if contract else None,
                "status": contract.status if contract else None,
            },

            "queue": {
                "status": queue.status if queue else None,
                "error": queue.error if queue else None,
            },

            "diagnostic_status": diagnostic_status,

            "problems": problems,
        }
