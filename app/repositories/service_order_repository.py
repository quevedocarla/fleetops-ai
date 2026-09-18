from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.processing_queue import ProcessingQueue
from app.models.service_order import ServiceOrder


class ServiceOrderRepository:

    @staticmethod
    def get_service_order(
        db: Session,
        service_order_id: int,
    ):
        return db.scalar(
            select(ServiceOrder)
            .where(ServiceOrder.id == service_order_id)
        )

    @staticmethod
    def get_contract(
        db: Session,
        contract_id: int,
    ):
        return db.scalar(
            select(Contract)
            .where(Contract.id == contract_id)
        )

    @staticmethod
    def get_latest_queue(
        db: Session,
        service_order_id: int,
    ):
        return db.scalar(
            select(ProcessingQueue)
            .where(
                ProcessingQueue.service_order_id
                == service_order_id
            )
            .order_by(ProcessingQueue.id.desc())
            .limit(1)
        )
