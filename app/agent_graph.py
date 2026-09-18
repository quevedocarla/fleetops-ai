import argparse
import asyncio
import json
import os
import selectors
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from mcp import Client
from ollama import chat

from app.mcp_server import mcp


# ============================================================
# CONFIGURACAO
# ============================================================

load_dotenv()

MODEL = "qwen2.5:3b"

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL nao foi encontrada no arquivo .env"
    )


# ============================================================
# URL DO POSTGRES PARA O CHECKPOINTER
# ============================================================
#
# SQLAlchemy pode utilizar:
#
# postgresql+psycopg://...
#
# O AsyncPostgresSaver/Psycopg espera:
#
# postgresql://...
#
# ============================================================

CHECKPOINT_DB_URL = (
    DATABASE_URL
    .replace(
        "postgresql+psycopg://",
        "postgresql://",
    )
    .replace(
        "postgresql+psycopg2://",
        "postgresql://",
    )
)


# ============================================================
# STATE
# ============================================================

class AgentState(TypedDict, total=False):
    service_order_id: int
    question: str
    diagnostic: str
    knowledge: str
    answer: str


# ============================================================
# FUNCAO AUXILIAR PARA RETORNO MCP
# ============================================================

def mcp_result_to_text(result) -> str:
    """
    Converte o retorno de uma Tool MCP para texto.
    """

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

        text = getattr(
            block,
            "text",
            None,
        )

        if text:
            return text

    return ""


# ============================================================
# CONDITIONAL ROUTING
# ============================================================

def route_after_diagnostic(
    state: AgentState,
) -> str:
    """
    Decide qual caminho o LangGraph deve seguir.

    BLOCKED:
        consulta conhecimento via RAG.

    Outros status:
        vai diretamente para a resposta.
    """

    diagnostic = json.loads(
        state["diagnostic"]
    )

    status = diagnostic.get(
        "diagnostic_status"
    )

    print(
        f"\nDECISAO - Status encontrado: {status}"
    )

    if status == "BLOCKED":

        print(
            "DECISAO - OS bloqueada. "
            "Consultando conhecimento..."
        )

        return "knowledge"

    print(
        "DECISAO - Nao precisa consultar "
        "conhecimento adicional."
    )

    return "answer"


# ============================================================
# NODE 1 - DIAGNOSTICO
# ============================================================

async def get_diagnostic(
    state: AgentState,
) -> dict:
    """
    Busca os fatos atuais da Ordem de Servico
    utilizando a Tool MCP.
    """

    print(
        "\nNODE 1 - Buscando diagnostico..."
    )

    print(
        f"OS recuperada do State: "
        f"{state['service_order_id']}"
    )

    async with Client(mcp) as client:

        result = await client.call_tool(
            "get_service_order_diagnostic",
            {
                "service_order_id":
                    state["service_order_id"]
            },
        )

    diagnostic = mcp_result_to_text(
        result
    )

    # Zeramos knowledge porque uma nova consulta
    # de diagnostico nao deve reutilizar conhecimento
    # antigo indevidamente.
    return {
        "diagnostic": diagnostic,
        "knowledge": "",
    }


# ============================================================
# NODE 2 - RAG
# ============================================================

async def get_knowledge(
    state: AgentState,
) -> dict:
    """
    Consulta regras e documentacao utilizando RAG.
    """

    print(
        "\nNODE 2 - Buscando conhecimento via RAG..."
    )

    async with Client(mcp) as client:

        result = await client.call_tool(
            "search_knowledge",
            {
                "query":
                    state["diagnostic"],
                "limit": 3,
            },
        )

    knowledge = mcp_result_to_text(
        result
    )

    return {
        "knowledge": knowledge
    }


# ============================================================
# NODE 3 - RESPOSTA
# ============================================================

async def generate_answer(
    state: AgentState,
) -> dict:
    """
    Gera a resposta final utilizando o LLM local.
    """

    print(
        "\nNODE 3 - Gerando resposta..."
    )

    question = state.get(
        "question",
        "Explique a situacao desta Ordem de Servico.",
    )

    knowledge = (
        state.get("knowledge")
        or
        "Nenhuma regra adicional precisou ser consultada."
    )

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Voce e um assistente de diagnostico "
                    "operacional. "
                    "OS significa Ordem de Servico. "
                    "Use somente os fatos e regras fornecidos. "
                    "Nao invente informacoes. "
                    "Nao presuma informacoes ausentes. "
                    "Responda diretamente ao que foi perguntado. "
                    "Se perguntarem qual e o contrato, "
                    "informe explicitamente o numero do contrato. "
                    "Se houver fila com status PROCESSED, "
                    "diga que a fila foi processada, "
                    "e nao que a OS nao possui fila. "
                    "Responda em portugues de forma clara "
                    "e objetiva."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"PERGUNTA:\n"
                    f"{question}\n\n"

                    f"OS EM CONTEXTO:\n"
                    f"{state['service_order_id']}\n\n"

                    f"DIAGNOSTICO:\n"
                    f"{state['diagnostic']}\n\n"

                    f"CONHECIMENTO:\n"
                    f"{knowledge}\n\n"

                    "Responda somente com base "
                    "nas informacoes fornecidas."
                ),
            },
        ],
        options={
            "temperature": 0,
        },
    )

    return {
        "answer":
            response.message.content
    }


# ============================================================
# CONSTRUCAO DO LANGGRAPH
# ============================================================

builder = StateGraph(
    AgentState
)


# ------------------------------------------------------------
# NODES
# ------------------------------------------------------------

builder.add_node(
    "diagnostic",
    get_diagnostic,
)

builder.add_node(
    "knowledge",
    get_knowledge,
)

builder.add_node(
    "answer",
    generate_answer,
)


# ------------------------------------------------------------
# EDGES
# ------------------------------------------------------------

builder.add_edge(
    START,
    "diagnostic",
)


builder.add_conditional_edges(
    "diagnostic",
    route_after_diagnostic,
    {
        "knowledge": "knowledge",
        "answer": "answer",
    },
)


builder.add_edge(
    "knowledge",
    "answer",
)


builder.add_edge(
    "answer",
    END,
)


# ============================================================
# THREAD PERSISTENTE
# ============================================================
#
# Esse ID identifica a conversa.
#
# O mesmo thread_id sera utilizado no SAVE
# e depois no RESUME.
#
# ============================================================

THREAD_ID = "fleetops-persistente-001"


# ============================================================
# MAIN
# ============================================================

async def main():

    # --------------------------------------------------------
    # Argumentos:
    #
    # python -m app.agent_graph save
    #
    # ou
    #
    # python -m app.agent_graph resume
    # --------------------------------------------------------

    parser = argparse.ArgumentParser(
        description=(
            "Teste de checkpoint persistente "
            "do FleetOps AI."
        )
    )

    parser.add_argument(
        "mode",
        choices=[
            "save",
            "resume",
        ],
        help=(
            "save grava o contexto; "
            "resume recupera o contexto."
        ),
    )

    args = parser.parse_args()


    # ========================================================
    # CONFIGURACAO DA THREAD
    # ========================================================

    config = {
        "configurable": {
            "thread_id":
                THREAD_ID
        }
    }


    # ========================================================
    # POSTGRES CHECKPOINTER
    # ========================================================

    async with AsyncPostgresSaver.from_conn_string(
        CHECKPOINT_DB_URL
    ) as checkpointer:

        # ----------------------------------------------------
        # Cria as tabelas do LangGraph no PostgreSQL.
        #
        # Nas proximas execucoes, o setup reconhece
        # as migrations ja aplicadas.
        # ----------------------------------------------------

        await checkpointer.setup()


        # ----------------------------------------------------
        # Agora o grafo usa PostgreSQL como checkpointer.
        # ----------------------------------------------------

        graph = builder.compile(
            checkpointer=checkpointer
        )


        # ====================================================
        # SAVE
        # ====================================================

        if args.mode == "save":

            print(
                "\n========================================"
            )

            print(
                "PROCESSO 1 - SALVANDO CONTEXTO"
            )

            print(
                "========================================"
            )

            print(
                f"THREAD: {THREAD_ID}"
            )

            print(
                "Usuario: Analise a OS 10235."
            )


            result = await graph.ainvoke(
                {
                    "service_order_id": 10235,
                    "question": (
                        "Analise a OS 10235 "
                        "e explique sua situacao."
                    ),
                },
                config=config,
            )


            print(
                "\n========================================"
            )

            print(
                "RESPOSTA"
            )

            print(
                "========================================"
            )

            print(
                result["answer"]
            )


            print(
                "\n========================================"
            )

            print(
                "STATE SALVO"
            )

            print(
                "========================================"
            )

            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )
            )


            print(
                "\n----------------------------------------"
            )

            print(
                "CHECKPOINT SALVO NO POSTGRESQL"
            )

            print(
                "O processo pode ser encerrado."
            )

            print(
                "Depois execute:"
            )

            print(
                "python -m app.agent_graph resume"
            )

            print(
                "----------------------------------------"
            )


        # ====================================================
        # RESUME
        # ====================================================

        elif args.mode == "resume":

            print(
                "\n========================================"
            )

            print(
                "PROCESSO 2 - RECUPERANDO CONTEXTO"
            )

            print(
                "========================================"
            )

            print(
                f"THREAD: {THREAD_ID}"
            )

            print(
                "Usuario: Qual e o contrato dela?"
            )


            # ------------------------------------------------
            # IMPORTANTE:
            #
            # Nao enviamos:
            #
            # service_order_id = 10235
            #
            # Esperamos que o LangGraph recupere esse valor
            # do checkpoint persistido no PostgreSQL.
            # ------------------------------------------------

            result = await graph.ainvoke(
                {
                    "question":
                        "Qual e o contrato dela?"
                },
                config=config,
            )


            print(
                "\n========================================"
            )

            print(
                "RESPOSTA"
            )

            print(
                "========================================"
            )

            print(
                result["answer"]
            )


            print(
                "\n========================================"
            )

            print(
                "STATE RECUPERADO DO POSTGRESQL"
            )

            print(
                "========================================"
            )

            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )
            )


# ============================================================
# EVENT LOOP PARA WINDOWS
# ============================================================
#
# No Windows, Python utiliza por padrao:
#
# ProactorEventLoop
#
# O Psycopg async precisa de:
#
# SelectorEventLoop
#
# ============================================================

def create_selector_event_loop():
    """
    Cria um SelectorEventLoop compativel
    com Psycopg async no Windows.
    """

    selector = selectors.SelectSelector()

    loop = asyncio.SelectorEventLoop(
        selector
    )

    asyncio.set_event_loop(
        loop
    )

    return loop


# ============================================================
# EXECUCAO
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main(),
        loop_factory=create_selector_event_loop,
    )