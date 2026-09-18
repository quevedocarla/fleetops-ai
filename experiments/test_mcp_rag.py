import asyncio

from mcp import Client

from app.mcp_server import mcp


async def main():
    async with Client(mcp) as client:

        print("1 - Tools publicadas:")

        tools = await client.list_tools()

        for tool in tools.tools:
            print(f"- {tool.name}")

        print("\n2 - Consultando conhecimento via MCP...")

        result = await client.call_tool(
            "search_knowledge",
            {
                "query": (
                    "Qual regra se aplica a uma OS de instalacao "
                    "com contrato inativo?"
                ),
                "limit": 3,
            },
        )

        print("\n3 - Resultado:")

        for block in result.content:
            text = getattr(block, "text", None)

            if text:
                print(text)


if __name__ == "__main__":
    asyncio.run(main())
