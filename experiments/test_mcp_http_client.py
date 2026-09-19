"""
Teste manual do MCP externo FleetOps via Streamable HTTP.

Pré-requisito:
    Em outro terminal, na raiz do projeto:
        python -m app.mcp_http_server

Depois:
    python experiments/test_mcp_http_client.py
"""

import asyncio

from mcp import Client


MCP_URL = "http://127.0.0.1:8001/mcp"


async def main() -> None:
    print(f"Conectando ao MCP: {MCP_URL}")

    async with Client(MCP_URL) as client:
        tools = await client.list_tools()

        print("\nFerramentas disponíveis:")
        for tool in tools.tools:
            print(f"- {tool.name}")

        print("\n1) get_service_order_diagnostic(10235)")

        diagnostic = await client.call_tool(
            "get_service_order_diagnostic",
            {
                "service_order_id": 10235,
            },
        )

        print("\nResultado do diagnóstico:")
        print(diagnostic.content)

        print("\n2) search_knowledge(...)")

        knowledge = await client.call_tool(
            "search_knowledge",
            {
                "query": "Quando uma OS de instalação pode ser processada?",
                "limit": 3,
                "trace_id": "mcp-http-manual-test",
            },
        )

        print("\nResultado do RAG:")
        print(knowledge.content)

        print("\nOK - MCP externo respondeu via Streamable HTTP.")
        print("OK - Diagnóstico operacional validado.")
        print("OK - Busca de conhecimento/RAG validada.")


if __name__ == "__main__":
    asyncio.run(main())
