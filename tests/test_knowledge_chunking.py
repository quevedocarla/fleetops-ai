from app.services.knowledge_chunking import (
    build_source_name,
    chunk_knowledge_markdown,
)


def test_rule_id_stays_with_description():

    text = """
# Regras de Contratos

CONTR-001

Uma Ordem de Servico de instalacao somente pode ser processada
quando o contrato relacionado estiver com status ACTIVE.

Caso o contrato esteja INACTIVE, a Ordem de Servico deve permanecer
bloqueada ate que a situacao contratual seja regularizada.
"""


    chunks = (
        chunk_knowledge_markdown(
            text
        )
    )


    rule_chunks = [
        chunk
        for chunk in chunks
        if "CONTR-001" in chunk
    ]


    assert len(
        rule_chunks
    ) == 1


    assert (
        "Uma Ordem de Servico de instalacao"
        in rule_chunks[0]
    )


def test_rule_id_is_not_isolated():

    text = """
CONTR-001

Descricao principal da regra.
"""


    chunks = (
        chunk_knowledge_markdown(
            text
        )
    )


    assert chunks == [
        (
            "CONTR-001\n\n"
            "Descricao principal da regra."
        )
    ]


def test_normal_paragraphs_remain_separate():

    text = """
Primeiro paragrafo.

Segundo paragrafo.

Terceiro paragrafo.
"""


    chunks = (
        chunk_knowledge_markdown(
            text
        )
    )


    assert chunks == [
        "Primeiro paragrafo.",
        "Segundo paragrafo.",
        "Terceiro paragrafo.",
    ]


def test_markdown_rule_header_is_merged():

    text = """
## CONTR-001

Uma OS de instalacao exige contrato ativo.
"""


    chunks = (
        chunk_knowledge_markdown(
            text
        )
    )


    assert len(
        chunks
    ) == 1


    assert (
        "CONTR-001"
        in chunks[0]
    )


    assert (
        "contrato ativo"
        in chunks[0]
    )


def test_r121_style_rule_is_merged():

    text = """
R121

Negociacao com contrato ja gerado
nao pode ser reaberta.
"""


    chunks = (
        chunk_knowledge_markdown(
            text
        )
    )


    assert len(
        chunks
    ) == 1


    assert (
        "R121"
        in chunks[0]
    )


def test_source_name_keeps_current_pattern():

    assert (
        build_source_name(
            "contracts.md",
            3,
        )
        == "contracts.md#chunk-3"
    )
