from ollama import embed
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.knowledge_document import KnowledgeDocument


MODEL = "embeddinggemma"

QUESTION = (
    "O que deve acontecer com uma OS de instalacao "
    "quando o contrato esta inativo?"
)


def main():
    db = SessionLocal()

    try:
        print("1 - Pergunta:")
        print(QUESTION)

        print("\n2 - Gerando embedding da pergunta...")

        response = embed(
            model=MODEL,
            input=QUESTION,
        )

        query_vector = response.embeddings[0]

        distance = (
            KnowledgeDocument.embedding
            .cosine_distance(query_vector)
        )

        statement = (
            select(
                KnowledgeDocument,
                distance.label("distance"),
            )
            .order_by(distance)
            .limit(3)
        )

        rows = db.execute(statement).all()

        print("\n3 - Documentos mais relevantes:")

        for document, dist in rows:

            similarity = 1 - dist

            print(
                "\n-------------------------"
            )

            print(
                f"Fonte: {document.source}"
            )

            print(
                f"Similaridade: "
                f"{similarity:.4f}"
            )

            print(
                f"Conteudo:\n{document.content}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()
