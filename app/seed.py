from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.contract import Contract
from app.models.processing_queue import ProcessingQueue
from app.models.service_order import ServiceOrder


def seed():
    db = SessionLocal()

    try:
        existe = db.scalar(
            select(Contract).where(Contract.id == 2001)
        )

        if existe:
            print("Dados ficticios ja existem.")
            return

        contracts = [
            Contract(
                id=2001,
                customer_name="Empresa Alpha",
                status="ACTIVE",
            ),
            Contract(
                id=2002,
                customer_name="Empresa Beta",
                status="INACTIVE",
            ),
            Contract(
                id=2003,
                customer_name="Empresa Gamma",
                status="ACTIVE",
            ),
        ]

        service_orders = [
            ServiceOrder(
                id=10234,
                contract_id=2001,
                vehicle_plate="ABC1D23",
                type="INSTALLATION",
                status="PENDING",
            ),
            ServiceOrder(
                id=10235,
                contract_id=2002,
                vehicle_plate="DEF4G56",
                type="INSTALLATION",
                status="PENDING",
            ),
            ServiceOrder(
                id=10236,
                contract_id=2003,
                vehicle_plate="GHI7J89",
                type="MAINTENANCE",
                status="COMPLETED",
            ),
            ServiceOrder(
                id=10237,
                contract_id=2001,
                vehicle_plate="JKL1M23",
                type="CANCELLATION",
                status="PENDING",
            ),
        ]

        queues = [
            ProcessingQueue(
                service_order_id=10234,
                action="PROCESS_INSTALLATION",
                status="PENDING",
                error=None,
            ),
            ProcessingQueue(
                service_order_id=10235,
                action="PROCESS_INSTALLATION",
                status="ERROR",
                error="Contract is inactive",
            ),
            ProcessingQueue(
                service_order_id=10236,
                action="PROCESS_MAINTENANCE",
                status="PROCESSED",
                error=None,
            ),
        ]

        db.add_all(contracts)
        db.add_all(service_orders)

        db.flush()

        db.add_all(queues)

        db.commit()

        print("Dados ficticios criados com sucesso!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()
