import re


RULE_ID_PATTERN = re.compile(
    r"^(?:#{1,6}\s*)?"
    r"(?:REGRA\s*[:\-]?\s*)?"
    r"(?P<rule_id>[A-Z][A-Z0-9_]*-\d{2,}|R\d{3})"
    r"(?:\s*[:\-]\s*(?P<title>.*))?$",
    flags=re.IGNORECASE,
)


def _normalize_block(
    block: str,
) -> str:
    """
    Remove espacos excedentes nas extremidades
    sem destruir as quebras internas do bloco.
    """

    lines = [
        line.rstrip()
        for line in block.strip().splitlines()
    ]

    return "\n".join(lines).strip()


def _split_blocks(
    text: str,
) -> list[str]:
    """
    Divide Markdown por linhas em branco.

    A diferenca para um split simples e que
    centralizamos a regra aqui para conseguir
    evoluir o chunking sem espalhar logica
    pela ingestao.
    """

    if not text:
        return []

    raw_blocks = re.split(
        r"\n\s*\n+",
        text.replace(
            "\r\n",
            "\n",
        ),
    )

    return [
        normalized
        for block in raw_blocks
        if (
            normalized := _normalize_block(
                block
            )
        )
    ]


def _is_rule_header(
    block: str,
) -> bool:
    """
    Identifica blocos que sao apenas um
    identificador/cabecalho de regra.

    Exemplos:
    CONTR-001
    ## CONTR-001
    Regra CONTR-001
    R121
    """

    single_line = " ".join(
        line.strip()
        for line in block.splitlines()
    )

    match = RULE_ID_PATTERN.match(
        single_line
    )

    if not match:
        return False

    title = (
        match.group(
            "title"
        )
        or ""
    ).strip()

    # Se existe um texto longo depois do ID,
    # o bloco ja contem conteudo suficiente.
    return len(title) <= 80


def chunk_knowledge_markdown(
    text: str,
) -> list[str]:
    """
    Gera chunks sem separar o ID da regra
    da descricao imediatamente seguinte.

    Problema resolvido:
        CONTR-001

        Uma Ordem de Servico de instalacao...

    Antes:
        chunk 1 -> CONTR-001
        chunk 2 -> Uma Ordem de Servico...

    Agora:
        chunk 1 ->
            CONTR-001

            Uma Ordem de Servico...

    Os demais paragrafos continuam independentes,
    preservando o comportamento simples do RAG.
    """

    blocks = _split_blocks(
        text
    )

    chunks: list[str] = []

    index = 0


    while index < len(
        blocks
    ):

        current = blocks[
            index
        ]


        if (
            _is_rule_header(
                current
            )
            and
            index + 1 < len(
                blocks
            )
        ):

            next_block = blocks[
                index + 1
            ]


            combined = (
                f"{current}\n\n"
                f"{next_block}"
            )


            chunks.append(
                combined
            )


            index += 2

            continue


        chunks.append(
            current
        )


        index += 1


    return chunks


def build_source_name(
    filename: str,
    chunk_index: int,
) -> str:
    """
    Mantem o formato de source ja usado
    pelo FleetOps:
        contracts.md#chunk-1
    """

    return (
        f"{filename}"
        f"#chunk-{chunk_index}"
    )
