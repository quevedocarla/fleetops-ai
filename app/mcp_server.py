from mcp.server import MCPServer

from app.rag.knowledge_search import (
    search_knowledge as search_knowledge_rag,
)

from app.tools.service_order_tools import (
    get_service_order_diagnostic as diagnose_service_order,
)


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer(
    "FleetOps MCP Server"
)


# ============================================================
# TOOL 1 - DIAGNOSTICO DA OS
# ============================================================

@mcp.tool()
def get_service_order_diagnostic(
    service_order_id: int,
) -> str:
    """
    Busca o diagnostico operacional de uma Ordem de Servico.

    Retorna dados atuais da OS,
    contrato, fila e problemas encontrados.
    """

    return diagnose_service_order(
        service_order_id
    )


# ============================================================
# TOOL 2 - BUSCA DE CONHECIMENTO / RAG
# ============================================================

@mcp.tool()
def search_knowledge(
    query: str,
    limit: int = 3,
    trace_id: str | None = None,
) -> str:
    """
    Busca regras e conhecimento na base vetorial.

    O trace_id permite correlacionar esta execucao
    com a requisicao HTTP e com os nodes do LangGraph.
    """

    return search_knowledge_rag(
        query=query,
        limit=limit,
        trace_id=trace_id,
    )