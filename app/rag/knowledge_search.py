import json
import os
import re
import time
import unicodedata
from collections import defaultdict

from ollama import embed
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.observability import log_event
from app.models.knowledge_document import KnowledgeDocument


# ============================================================
# CONFIGURACAO
# ============================================================

EMBEDDING_MODEL = "embeddinggemma"

RAG_CANDIDATE_LIMIT = int(
    os.getenv(
        "RAG_CANDIDATE_LIMIT",
        "12",
    )
)

RAG_VECTOR_WEIGHT = float(
    os.getenv(
        "RAG_VECTOR_WEIGHT",
        "0.70",
    )
)

RAG_LEXICAL_WEIGHT = float(
    os.getenv(
        "RAG_LEXICAL_WEIGHT",
        "0.30",
    )
)

RAG_MAX_CHUNKS_PER_SOURCE = int(
    os.getenv(
        "RAG_MAX_CHUNKS_PER_SOURCE",
        "2",
    )
)


# Palavras que pouco ajudam a diferenciar regras/documentos.
STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "ela",
    "ele",
    "em",
    "esta",
    "este",
    "isso",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "para",
    "por",
    "que",
    "quando",
    "se",
    "ser",
    "uma",
    "um",
}


# Normalizacao lexical simples e deterministica para termos
# operacionais frequentes. Nao e um stemmer generico.
DOMAIN_PREFIXES = {
    "bloque": "bloqueio",
    "cancel": "cancelamento",
    "conclu": "conclusao",
    "contrat": "contrato",
    "diagnost": "diagnostico",
    "imped": "impedir",
    "instal": "instalacao",
    "manut": "manutencao",
    "pend": "pendente",
    "process": "processamento",
    "regular": "regularizacao",
    "servic": "servico",
}


# ============================================================
# AUXILIARES
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


def normalize_lexical_text(text: str) -> str:
    """
    Remove acentos e normaliza caixa/pontuacao.
    """

    normalized = unicodedata.normalize(
        "NFD",
        text or "",
    )

    normalized = "".join(
        char
        for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    normalized = normalized.lower()

    # "OS" no dominio equivale conceitualmente a
    # Ordem de Servico. Fazemos a expansao antes da tokenizacao.
    normalized = re.sub(
        r"\bos\b",
        " ordem servico ",
        normalized,
    )

    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        normalized,
    )

    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()


def normalize_domain_token(token: str) -> str:
    """
    Agrupa apenas familias lexicais do dominio que sao
    importantes para recuperar regras operacionais.
    """

    for prefix, canonical in DOMAIN_PREFIXES.items():
        if token.startswith(prefix):
            return canonical

    return token


def lexical_tokens(text: str) -> set[str]:
    """
    Tokeniza o texto para o reranking lexical.
    """

    normalized = normalize_lexical_text(text)

    tokens = set()

    for token in normalized.split():
        if (
            not token
            or token in STOPWORDS
            or len(token) <= 2
        ):
            continue

        tokens.add(
            normalize_domain_token(token)
        )

    return tokens


def lexical_score(
    query: str,
    content: str,
) -> float:
    """
    Mede cobertura dos termos relevantes da pergunta
    pelo chunk.

    1.0 = todos os termos relevantes da pergunta aparecem
    no chunk apos normalizacao de dominio.
    """

    query_tokens = lexical_tokens(query)

    if not query_tokens:
        return 0.0

    content_tokens = lexical_tokens(content)

    overlap = (
        query_tokens
        &
        content_tokens
    )

    return len(overlap) / len(query_tokens)


def source_document(source: str) -> str:
    """
    contracts.md#chunk-2 -> contracts.md
    """

    return (
        source
        or ""
    ).split(
        "#",
        1,
    )[0]


def rerank_candidates(
    query: str,
    candidates: list[dict],
    limit: int,
) -> list[dict]:
    """
    Hybrid reranking:

      vector similarity
        +
      lexical coverage
        +
      source diversity

    O score vetorial continua disponivel em `similarity`.
    O score final usado apenas para ordenacao fica em
    `retrieval_score`.
    """

    scored = []

    for original_rank, candidate in enumerate(
        candidates,
        start=1,
    ):
        similarity = float(
            candidate.get(
                "similarity",
                0.0,
            )
        )

        lex_score = lexical_score(
            query,
            candidate.get(
                "content",
                "",
            ),
        )

        retrieval_score = (
            RAG_VECTOR_WEIGHT
            * similarity
            +
            RAG_LEXICAL_WEIGHT
            * lex_score
        )

        enriched = dict(candidate)

        enriched[
            "lexical_score"
        ] = round(
            lex_score,
            4,
        )

        enriched[
            "retrieval_score"
        ] = round(
            retrieval_score,
            4,
        )

        enriched[
            "_original_rank"
        ] = original_rank

        scored.append(
            enriched
        )

    scored.sort(
        key=lambda item: (
            -item[
                "retrieval_score"
            ],
            item[
                "_original_rank"
            ],
        )
    )

    selected = []
    source_counts = defaultdict(int)

    # Primeira passagem: diversidade leve.
    for candidate in scored:
        document_name = source_document(
            candidate.get(
                "source",
                "",
            )
        )

        if (
            source_counts[
                document_name
            ]
            >=
            RAG_MAX_CHUNKS_PER_SOURCE
        ):
            continue

        selected.append(
            candidate
        )

        source_counts[
            document_name
        ] += 1

        if len(selected) >= limit:
            break

    # Segunda passagem: se a diversidade impedir preencher
    # o limite, completa com os melhores restantes.
    if len(selected) < limit:
        selected_sources = {
            (
                item.get("source"),
                item.get("_original_rank"),
            )
            for item in selected
        }

        for candidate in scored:
            identity = (
                candidate.get("source"),
                candidate.get(
                    "_original_rank"
                ),
            )

            if identity in selected_sources:
                continue

            selected.append(
                candidate
            )

            if len(selected) >= limit:
                break

    for item in selected:
        item.pop(
            "_original_rank",
            None,
        )

    return selected


# ============================================================
# BUSCA RAG
# ============================================================

def search_knowledge(
    query: str,
    limit: int = 3,
    trace_id: str | None = None,
) -> str:
    """
    Faz busca hibrida na base de conhecimento.

    Etapas:

        1. Gera embedding da pergunta
        2. Busca pool de candidatos no pgvector
        3. Aplica reranking lexical
        4. Aplica diversidade leve de fonte
        5. Retorna apenas o top N solicitado
    """

    total_start = time.perf_counter()

    # ========================================================
    # 1. EMBEDDING
    # ========================================================

    embedding_start = time.perf_counter()

    embedding_response = embed(
        model=EMBEDDING_MODEL,
        input=query,
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
    # 2. PGVECTOR - CANDIDATE POOL
    # ========================================================

    vector_search_start = (
        time.perf_counter()
    )

    candidate_limit = max(
        RAG_CANDIDATE_LIMIT,
        limit * 4,
        limit,
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
            candidate_limit
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
        limit=candidate_limit,
        requested_limit=limit,
        results_count=
            len(rows),
        duration_ms=
            vector_search_duration,
    )

    # ========================================================
    # 3. MONTA CANDIDATOS
    # ========================================================

    candidate_results = []

    for document, distance_value in rows:
        similarity = (
            1
            -
            float(
                distance_value
            )
        )

        candidate_results.append(
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

    # ========================================================
    # 4. HYBRID RERANK
    # ========================================================

    rerank_start = (
        time.perf_counter()
    )

    results = rerank_candidates(
        query=query,
        candidates=
            candidate_results,
        limit=limit,
    )

    rerank_duration = round(
        (
            time.perf_counter()
            -
            rerank_start
        )
        * 1000,
        2,
    )

    log_event(
        "rag_rerank_completed",
        trace_id=trace_id,
        strategy=
            "vector_lexical_source_diversity",
        candidate_count=
            len(candidate_results),
        final_count=
            len(results),
        vector_weight=
            RAG_VECTOR_WEIGHT,
        lexical_weight=
            RAG_LEXICAL_WEIGHT,
        max_chunks_per_source=
            RAG_MAX_CHUNKS_PER_SOURCE,
        duration_ms=
            rerank_duration,
    )

    # ========================================================
    # 5. SERIALIZACAO
    # ========================================================

    serialize_start = (
        time.perf_counter()
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
        rerank_ms=
            rerank_duration,
        serialization_ms=
            serialize_duration,
        total_ms=
            total_duration,
        results_count=
            len(results),
    )

    return result_json
