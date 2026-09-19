from app.rag.knowledge_search import (
    lexical_score,
    lexical_tokens,
    rerank_candidates,
    source_document,
)


def test_os_is_normalized_as_service_order_terms():
    tokens = lexical_tokens(
        "Quando uma OS de instalação pode ser processada?"
    )

    assert "ordem" in tokens
    assert "servico" in tokens
    assert "instalacao" in tokens
    assert "processamento" in tokens


def test_contract_rule_has_stronger_lexical_coverage():
    query = (
        "Quando uma OS de instalação "
        "pode ser processada?"
    )

    contract = (
        "REGRA CONTR-001 "
        "Uma Ordem de Servico de instalacao "
        "somente pode ser processada quando "
        "o contrato relacionado estiver ACTIVE."
    )

    troubleshooting = (
        "Diagnóstico de erro de processamento de OS"
    )

    assert (
        lexical_score(
            query,
            contract,
        )
        >
        lexical_score(
            query,
            troubleshooting,
        )
    )


def test_source_document_removes_chunk_suffix():
    assert (
        source_document(
            "contracts.md#chunk-2"
        )
        ==
        "contracts.md"
    )


def test_rerank_promotes_specific_contract_rule_into_top3():
    query = (
        "Quando uma OS de instalação "
        "pode ser processada?"
    )

    candidates = [
        {
            "source": "troubleshooting.md#chunk-5",
            "similarity": 0.5920,
            "content": (
                "Diagnóstico de erro de "
                "processamento de OS"
            ),
        },
        {
            "source": "processing.md#chunk-1",
            "similarity": 0.5908,
            "content": (
                "Regras de Processamento de OS"
            ),
        },
        {
            "source": "troubleshooting.md#chunk-9",
            "similarity": 0.5435,
            "content": (
                "Uma OS com erro de processamento "
                "deve ser diagnosticada."
            ),
        },
        {
            "source": "contracts.md#chunk-2",
            "similarity": 0.4399,
            "content": (
                "REGRA CONTR-001 "
                "Uma Ordem de Servico de instalacao "
                "somente pode ser processada quando "
                "o contrato relacionado estiver ACTIVE."
            ),
        },
    ]

    results = rerank_candidates(
        query,
        candidates,
        limit=3,
    )

    sources = [
        item["source"]
        for item in results
    ]

    assert (
        "contracts.md#chunk-2"
        in sources
    )


def test_rerank_preserves_troubleshooting_as_top1():
    query = (
        "A OS está com erro de processamento. "
        "Onde encontro passos para diagnóstico?"
    )

    candidates = [
        {
            "source": "troubleshooting.md#chunk-5",
            "similarity": 0.8624,
            "content": (
                "Diagnóstico de erro de "
                "processamento de OS"
            ),
        },
        {
            "source": "troubleshooting.md#chunk-9",
            "similarity": 0.7874,
            "content": (
                "Uma OS com erro de processamento "
                "deve ser diagnosticada antes "
                "de qualquer tentativa de correção."
            ),
        },
        {
            "source": "processing.md#chunk-1",
            "similarity": 0.6063,
            "content": (
                "Regras de Processamento de OS"
            ),
        },
    ]

    results = rerank_candidates(
        query,
        candidates,
        limit=3,
    )

    assert (
        results[0]["source"]
        ==
        "troubleshooting.md#chunk-5"
    )


def test_rerank_limits_two_chunks_per_source_when_possible():
    query = "erro de processamento da OS"

    candidates = [
        {
            "source": "troubleshooting.md#chunk-1",
            "similarity": 0.90,
            "content": "erro processamento OS",
        },
        {
            "source": "troubleshooting.md#chunk-2",
            "similarity": 0.89,
            "content": "erro processamento OS",
        },
        {
            "source": "troubleshooting.md#chunk-3",
            "similarity": 0.88,
            "content": "erro processamento OS",
        },
        {
            "source": "processing.md#chunk-1",
            "similarity": 0.70,
            "content": "processamento OS",
        },
    ]

    results = rerank_candidates(
        query,
        candidates,
        limit=3,
    )

    documents = [
        source_document(
            item["source"]
        )
        for item in results
    ]

    assert documents.count(
        "troubleshooting.md"
    ) <= 2

    assert (
        "processing.md"
        in documents
    )
