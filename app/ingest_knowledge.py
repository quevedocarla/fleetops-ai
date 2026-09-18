from pathlib import Path

from ollama import embed
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.knowledge_document import KnowledgeDocument
from app.services.knowledge_chunking import (
    build_source_name,
    chunk_knowledge_markdown,
)


MODEL = "embeddinggemma"
DOCS_DIR = Path("docs")


KNOWLEDGE_FILES = {
    "contracts.md",
    "processing.md",
    "troubleshooting.md",
}


def main():
    db = SessionLocal()

    try:
        print(
            "1 - Limpando base de conhecimento anterior..."
        )

        db.execute(
            delete(
                KnowledgeDocument
            )
        )

        total = 0


        for file_path in sorted(
            DOCS_DIR.glob("*.md")
        ):

            if (
                file_path.name
                not in KNOWLEDGE_FILES
            ):

                print(
                    f"\nIgnorando arquivo "
                    f"nao operacional: "
                    f"{file_path.name}"
                )

                continue


            print(
                f"\n2 - Processando: "
                f"{file_path.name}"
            )


            text = file_path.read_text(
                encoding="utf-8-sig"
            )


            chunks = (
                chunk_knowledge_markdown(
                    text
                )
            )


            print(
                f"   {len(chunks)} "
                f"chunks identificados."
            )


            for index, chunk in enumerate(
                chunks,
                start=1,
            ):

                source = (
                    build_source_name(
                        file_path.name,
                        index,
                    )
                )


                print(
                    f"   Gerando embedding "
                    f"do chunk {index} "
                    f"({source})..."
                )


                response = embed(
                    model=MODEL,
                    input=chunk,
                )


                vector = (
                    response.embeddings[0]
                )


                document = (
                    KnowledgeDocument(
                        source=source,
                        content=chunk,
                        embedding=vector,
                    )
                )


                db.add(
                    document
                )


                total += 1


        db.commit()


        print(
            f"\n3 - Ingestao concluida. "
            f"{total} chunks gravados."
        )


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


if __name__ == "__main__":
    main()

