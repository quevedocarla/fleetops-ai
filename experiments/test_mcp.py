import asyncio

from mcp import Client

from app.mcp_server import mcp


async def main():
    print("1 - Conectando ao FleetOps MCP Server...")

    async with Client(mcp) as client:
        print("2 - Conexao MCP estabelecida.")

        tools = await client.list_tools()

        print("\n3 - Tools publicadas:")

        for tool in tools.tools:
            print(f"- {tool.name}")

        print(
            "\n4 - Chamando "
            "get_service_order_diagnostic..."
        )

        result = await client.call_tool(
            "get_service_order_diagnostic",
            {
                "service_order_id": 10235
            },
        )

        print("\n5 - Resultado retornado pelo MCP:")

        print("Erro:", result.is_error)

        if result.structured_content:
            print(result.structured_content)

        for block in result.content:
            text = getattr(
                block,
                "text",
                None,
            )

            if text:
                print(text)


if __name__ == "__main__":
    asyncio.run(main())
