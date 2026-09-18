from app.core.database import Base, engine

from app.models.contract import Contract
from app.models.processing_queue import ProcessingQueue
from app.models.service_order import ServiceOrder


def init_db():
    print("Criando tabelas...")

    Base.metadata.create_all(bind=engine)

    print("Tabelas criadas com sucesso!")


if __name__ == "__main__":
    init_db()