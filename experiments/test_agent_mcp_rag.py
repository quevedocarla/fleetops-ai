import asyncio
import json

from mcp import Client
from ollama import chat

from app.mcp_server import mcp


MODEL = "qwen2.5:3b"


def mcp_result_to_text(result) -> str:

    if result.structured_content:
        if "result" in result.structured_content:
            return str(
                result.structured_content["result"]
            )

        return json.dumps(
            result.structured_content,
            ensure_ascii=False,
        )

    for block in result.content:
        text = getattr(block, "text", None)

        if text:
            return text

    return "Sem resultado."


async def main():

    async with Client(mcp) as client:

        print("1 - Descobrindo tools MCP...")

        tools_result = await client.list_tools()

        ollama_tools = []

        for tool in tools_result.tools:

            print(f"- {tool.name}")

            ollama_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema,
                    },
                }
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "Voce e um assistente de diagnostico operacional. "
                    "OS significa Ordem de Servico. "
                    "Primeiro consulte dados atuais da OS usando "
                    "get_service_order_diagnostic. "
                    "Depois consulte regras e documentacao usando "
                    "search_knowledge. "
                    "Nao invente fatos nem regras. "
                    "Responda somente com base nas ferramentas."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Por que a OS 10235 esta bloqueada "
                    "e qual regra explica esse bloqueio?"
                ),
            },
        ]

        print("\n2 - Consultando diagnostico da OS via MCP...")

        diagnostic_result = await client.call_tool(
            "get_service_order_diagnostic",
            {
                "service_order_id": 10235
            },
        )

        diagnostic_text = mcp_result_to_text(
            diagnostic_result
        )

        print(diagnostic_text)

        messages.append(
            {
                "role": "user",
                "content": (
                    "DADOS ATUAIS DA OS:\n"
                    + diagnostic_text
                ),
            }
        )

        print("\n3 - Consultando regras via RAG/MCP...")

        knowledge_result = await client.call_tool(
            "search_knowledge",
            {
                "query": (
                    "OS de instalacao com contrato inativo "
                    "e fila de processamento com erro"
                ),
                "limit": 3,
            },
        )

        knowledge_text = mcp_result_to_text(
            knowledge_result
        )

        print(knowledge_text)

        messages.append(
            {
                "role": "user",
                "content": (
                    "REGRAS E DOCUMENTACAO RECUPERADAS:\n"
                    + knowledge_text
                ),
            }
        )

        print("\n4 - Gerando resposta final...")

        response = chat(
            model=MODEL,
            messages=messages,
            options={
                "temperature": 0,
            },
        )

        print("\n5 - Resposta do agente:")
        print(response.message.content)


if __name__ == "__main__":
    asyncio.run(main())
