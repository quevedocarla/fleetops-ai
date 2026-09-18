import asyncio
import json

from mcp import Client
from ollama import chat

from app.mcp_server import mcp


MODEL = "qwen2.5:3b"


def result_to_text(result) -> str:
    if result.structured_content:
        if "result" in result.structured_content:
            return str(result.structured_content["result"])

        return json.dumps(
            result.structured_content,
            ensure_ascii=False,
        )

    for block in result.content:
        text = getattr(block, "text", None)

        if text:
            return text

    return "A ferramenta nao retornou dados."


async def main():
    print("1 - Conectando ao MCP Server...")

    async with Client(mcp) as client:

        tools_result = await client.list_tools()

        print("2 - Tools descobertas via MCP:")

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
                    "Quando o usuario perguntar sobre uma OS especifica, "
                    "use obrigatoriamente uma ferramenta MCP antes de responder. "
                    "Nunca invente dados de contratos, filas ou OS. "
                    "Use somente as informacoes retornadas pelas ferramentas. "
                    "Responda em portugues, de forma curta e objetiva."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Por que a OS 10235 esta bloqueada?"
                ),
            },
        ]

        print("\n3 - Enviando pergunta ao Qwen...")

        response = chat(
            model=MODEL,
            messages=messages,
            tools=ollama_tools,
            options={
                "temperature": 0,
            },
        )

        messages.append(response.message)

        if not response.message.tool_calls:
            print("\nO modelo nao solicitou nenhuma tool.")
            print("Resposta:", response.message.content)
            return

        for call in response.message.tool_calls:

            print("\n4 - Tool escolhida pelo modelo:")
            print(call.function.name)

            print("\n5 - Argumentos:")
            print(call.function.arguments)

            print("\n6 - Executando tool via MCP...")

            result = await client.call_tool(
                call.function.name,
                call.function.arguments,
            )

            tool_text = result_to_text(result)

            print("\n7 - Resultado recebido do MCP:")
            print(tool_text)

            messages.append(
                {
                    "role": "tool",
                    "tool_name": call.function.name,
                    "content": tool_text,
                }
            )

        print("\n8 - Enviando evidencias de volta ao Qwen...")

        final_response = chat(
            model=MODEL,
            messages=messages,
            tools=ollama_tools,
            options={
                "temperature": 0,
            },
        )

        print("\n9 - Resposta final:")
        print(final_response.message.content)


if __name__ == "__main__":
    asyncio.run(main())
