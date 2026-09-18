import json
import time

from ollama import embed
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.observability import log_event
from app.models.knowledge_document import KnowledgeDocument


# ============================================================
# CONFIGURACAO
# ============================================================

EMBEDDING_MODEL = "embeddinggemma"


# ============================================================
# AUXILIAR
# ============================================================

def ns_to_ms(value) -> float:
    """
    Converte nanossegundos retornados pelo Ollama
    para milissegundos.
    """

    if not value:
        return 0.0

    return round(
        value / 1_000_000,
        2,
    )


# ============================================================
# BUSCA RAG
# ============================================================

def search_knowledge(
    query: str,
    limit: int = 3,
    trace_id: str | None = None,
) -> str:
    """
    Faz busca semantica na base de conhecimento.

    Etapas medidas:

        1. Gera embedding da pergunta
        2. Consulta vetorial no PostgreSQL/pgvector
        3. Monta o retorno JSON
    """

    total_start = time.perf_counter()


    # ========================================================
    # 1. EMBEDDING
    # ========================================================

    embedding_start = time.perf_counter()


    embedding_response = embed(
        model=EMBEDDING_MODEL,
        input=query,

        # Mantem o modelo carregado para os proximos RAGs.
        keep_alive="30m",
    )


    query_embedding = (
        embedding_response.embeddings[0]
    )


    embedding_duration = round(
        (
            time.perf_counter()
            -
            embedding_start
        )
        * 1000,
        2,
    )


    # --------------------------------------------------------
    # Metricas internas do Ollama
    # --------------------------------------------------------

    ollama_total_duration = getattr(
        embedding_response,
        "total_duration",
        0,
    )

    ollama_load_duration = getattr(
        embedding_response,
        "load_duration",
        0,
    )

    prompt_eval_count = getattr(
        embedding_response,
        "prompt_eval_count",
        0,
    )


    log_event(
        "rag_embedding_completed",

        trace_id=trace_id,

        model=EMBEDDING_MODEL,

        python_duration_ms=
            embedding_duration,

        ollama_total_ms=
            ns_to_ms(
                ollama_total_duration
            ),

        ollama_load_ms=
            ns_to_ms(
                ollama_load_duration
            ),

        prompt_tokens=
            prompt_eval_count,

        vector_dimensions=
            len(query_embedding),
    )


    # ========================================================
    # 2. PGVECTOR
    # ========================================================

    vector_search_start = (
        time.perf_counter()
    )


    distance = (
        KnowledgeDocument.embedding
        .cosine_distance(
            query_embedding
        )
    )


    statement = (
        select(
            KnowledgeDocument,
            distance.label(
                "distance"
            ),
        )
        .order_by(
            distance
        )
        .limit(
            limit
        )
    )


    with SessionLocal() as db:

        rows = (
            db.execute(
                statement
            )
            .all()
        )


    vector_search_duration = round(
        (
            time.perf_counter()
            -
            vector_search_start
        )
        * 1000,
        2,
    )


    log_event(
        "rag_vector_search_completed",

        trace_id=trace_id,

        database="postgresql",

        engine="pgvector",

        limit=limit,

        results_count=
            len(rows),

        duration_ms=
            vector_search_duration,
    )


    # ========================================================
    # 3. MONTA RESULTADO
    # ========================================================

    serialize_start = (
        time.perf_counter()
    )


    results = []


    for document, distance_value in rows:

        similarity = (
            1
            -
            float(
                distance_value
            )
        )


        results.append(
            {
                "source":
                    document.source,

                "similarity":
                    round(
                        similarity,
                        4,
                    ),

                "content":
                    document.content,
            }
        )


    result_json = json.dumps(
        results,
        ensure_ascii=False,
    )


    serialize_duration = round(
        (
            time.perf_counter()
            -
            serialize_start
        )
        * 1000,
        2,
    )


    # ========================================================
    # TOTAL DO RAG
    # ========================================================

    total_duration = round(
        (
            time.perf_counter()
            -
            total_start
        )
        * 1000,
        2,
    )


    log_event(
        "rag_search_completed",

        trace_id=trace_id,

        embedding_ms=
            embedding_duration,

        vector_search_ms=
            vector_search_duration,

        serialization_ms=
            serialize_duration,

        total_ms=
            total_duration,

        results_count=
            len(results),
    )


    return result_json