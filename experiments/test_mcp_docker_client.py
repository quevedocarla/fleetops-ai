"""
Teste manual do MCP Docker.

Pré-requisito:
    docker compose up -d --build

Depois:
    python experiments/test_mcp_docker_client.py
"""

import asyncio
import json

from mcp import Client


MCP_URL = "http://127.0.0.1:8001/mcp"


def print_text_content(result) -> None:
    for item in result.content:
        text = getattr(item, "text", None)
        if text is None:
            print(item)
            continue

        try:
            parsed = json.loads(text)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(text)


async def main() -> None:
    print(f"Conectando ao MCP Docker: {MCP_URL}")

    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools.tools]

        print("\nFerramentas disponíveis:")
        for name in tool_names:
            print(f"- {name}")

        expected = {
            "get_service_order_diagnostic",
            "search_knowledge",
        }

        missing = expected.difference(tool_names)
        if missing:
            raise RuntimeError(
                f"Tools ausentes no MCP Docker: {sorted(missing)}"
            )

        print("\n1) Diagnóstico da OS 10235")
        diagnostic = await client.call_tool(
            "get_service_order_diagnostic",
            {"service_order_id": 10235},
        )
        print_text_content(diagnostic)

        print("\n2) Busca RAG")
        knowledge = await client.call_tool(
            "search_knowledge",
            {
                "query": "Quando uma OS de instalação pode ser processada?",
                "limit": 3,
                "trace_id": "mcp-docker-manual-test",
            },
        )
        print_text_content(knowledge)

        print("\nOK - MCP Docker respondeu via Streamable HTTP.")
        print("OK - Diagnóstico operacional validado.")
        print("OK - Busca RAG validada.")


if __name__ == "__main__":
    asyncio.run(main())
