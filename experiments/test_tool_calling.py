from ollama import chat

from app.tools.service_order_tools import (
    get_service_order_diagnostic,
)


MODEL = "qwen2.5:3b"
 

messages = [
    {
        "role": "system",
        "content": (
            "Voce e um assistente de diagnostico operacional. "
            "OS significa Ordem de Servico. "
            "Para qualquer pergunta sobre uma OS especifica, "
            "voce DEVE consultar a ferramenta "
            "get_service_order_diagnostic antes de responder. "
            "Nunca invente o estado de uma OS, contrato ou fila. "
            "Use somente o resultado da ferramenta. "
            "Responda em portugues de forma curta e objetiva."
        ),
    },
   {
    "role": "user",
    "content": (
        "Consulte obrigatoriamente a ferramenta disponível "
        "para descobrir o diagnóstico da OS 10235. "
        "Somente depois responda por que ela está bloqueada."
    ),
},
]


print("1 - Pergunta enviada ao modelo...")


response = chat(
    model=MODEL,
    messages=messages,
    tools=[
        get_service_order_diagnostic,
    ],
    options={
        "temperature": 0,
    },
)


messages.append(response.message)


if not response.message.tool_calls:
    print(
        "O modelo nao chamou nenhuma ferramenta."
    )

    print(
        "Resposta:",
        response.message.content,
    )

    raise SystemExit()


for call in response.message.tool_calls:

    print("\n2 - Tool escolhida pelo modelo:")
    print(call.function.name)

    print("\n3 - Argumentos escolhidos:")
    print(call.function.arguments)

    if (
        call.function.name
        == "get_service_order_diagnostic"
    ):

        tool_result = (
            get_service_order_diagnostic(
                **call.function.arguments
            )
        )

    else:
        tool_result = (
            "Ferramenta desconhecida."
        )

    print("\n4 - Resultado da ferramenta:")
    print(tool_result)

    messages.append(
        {
            "role": "tool",
            "tool_name": call.function.name,
            "content": tool_result,
        }
    )


print(
    "\n5 - Enviando o resultado "
    "da ferramenta ao modelo..."
)


final_response = chat(
    model=MODEL,
    messages=messages,
    tools=[
        get_service_order_diagnostic,
    ],
    options={
        "temperature": 0,
    },
)


print("\n6 - Resposta final:")
print(final_response.message.content)