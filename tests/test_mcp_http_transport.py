import asyncio
import json
import os

from mcp import Client


MCP_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:8001/mcp",
)


def _extract_json(result):
    assert not getattr(result, "isError", False), (
        f"MCP tool retornou erro: {result.content}"
    )

    assert result.content, "MCP tool retornou conteúdo vazio."

    text = getattr(result.content[0], "text", None)
    assert text is not None, (
        f"Conteúdo MCP inesperado: {result.content}"
    )

    return json.loads(text)


async def _list_expected_tools():
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}

    assert "get_service_order_diagnostic" in names
    assert "search_knowledge" in names


async def _diagnostic_tool():
    async with Client(MCP_URL) as client:
        result = await client.call_tool(
            "get_service_order_diagnostic",
            {"service_order_id": 10235},
        )

    payload = _extract_json(result)

    assert payload["service_order"]["id"] == 10235
    assert payload["service_order"]["type"] == "INSTALLATION"
    assert payload["service_order"]["vehicle_plate"] == "DEF4G56"
    assert payload["contract"]["id"] == 2002
    assert payload["contract"]["status"] == "INACTIVE"
    assert payload["diagnostic_status"] == "BLOCKED"


async def _rag_tool():
    async with Client(MCP_URL) as client:
        result = await client.call_tool(
            "search_knowledge",
            {
                "query": (
                    "Quando uma OS de instalação "
                    "pode ser processada?"
                ),
                "limit": 3,
                "trace_id": "pytest-mcp-http",
            },
        )

    payload = _extract_json(result)

    assert isinstance(payload, list)
    assert payload, "A busca RAG não retornou resultados."

    combined = "\n".join(
        item.get("content", "")
        for item in payload
    )

    assert "CONTR-001" in combined
    assert "ACTIVE" in combined


def test_mcp_http_lists_expected_tools():
    asyncio.run(_list_expected_tools())


def test_mcp_http_diagnostic_tool():
    asyncio.run(_diagnostic_tool())


def test_mcp_http_rag_tool():
    asyncio.run(_rag_tool())
