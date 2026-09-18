from ollama import chat


print("1 - Chamando o modelo...")


response = chat(
    model="qwen2.5:1.5b-instruct",
    messages=[
        {
            "role": "system",
            "content": (
                "Voce e um assistente de operacoes. "
                "OS significa Ordem de Servico. "
                "Responda sempre em portugues, "
                "de maneira curta e objetiva."
            ),
        },
        {
            "role": "user",
            "content": (
                "A OS 10235 possui contrato inativo "
                "e fila de processamento com erro. "
                "Explique em uma unica frase por que "
                "ela esta bloqueada."
            ),
        },
    ],
)


print("2 - Resposta recebida:")
print(response.message.content)