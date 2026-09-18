import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


response = client.responses.create(
    model="gpt-5-mini",
    input="""
Você é um assistente de operações.

Responda em português e em uma única frase.

Teste:
A OS 10235 possui contrato inativo e fila de processamento com erro.
Explique por que ela está bloqueada.
""",
)


print(response.output_text)