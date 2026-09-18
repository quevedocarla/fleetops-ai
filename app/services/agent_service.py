import json
import os
import re
import time
import unicodedata

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from mcp import Client
from ollama import chat

from app.core.observability import log_event
from app.mcp_server import mcp
from app.intents.detector import (
    detect_direct_intent as detect_intent,
    extract_requested_service_order_type as detect_requested_service_order_type,
)
from app.intents.normalizer import (
    extract_service_order_id as extract_os_id,
    normalize_text as normalize_intent_text,
)
from app.policies.premise_validator import build_premise_response
from app.policies.scope_guard import (
    is_fleetops_scope as check_fleetops_scope,
)



MODEL = "qwen2.5:1.5b-instruct"


FORCE_DIAGNOSTIC_ERROR = (
    os.getenv("FLEETOPS_FORCE_DIAGNOSTIC_ERROR", "false").lower()
    == "true"
)

FORCE_RAG_ERROR = (
    os.getenv("FLEETOPS_FORCE_RAG_ERROR", "false").lower()
    == "true"
)

FORCE_LLM_ERROR = (
    os.getenv("FLEETOPS_FORCE_LLM_ERROR", "false").lower()
    == "true"
)


class AgentDependencyError(Exception):
    pass


class ServiceOrderNotFoundError(Exception):
    pass


class AgentState(TypedDict, total=False):
    trace_id: str
    thread_id: str
    service_order_id: int
    question: str
    diagnostic: str
    knowledge: str
    answer: str
    direct_intent: str | None
    degraded: bool
    warnings: list[str]
    response_mode: str
    knowledge_sources: list[dict]
    out_of_scope: bool


def ns_to_ms(value) -> float:
    if not value:
        return 0.0
    return round(value / 1_000_000, 2)


def normalize_text(text: str) -> str:
    return normalize_intent_text(text)



def normalize_user_answer(text: str) -> str:
    if not text:
        return text

    replacements = [
        (r"\best[aá] em estado INACTIVE\b", "está inativo"),
        (r"\best[aá] com status INACTIVE\b", "está inativo"),
        (r"\bem estado INACTIVE\b", "inativo"),
        (r"\bContract is inactive\b", "O contrato está inativo"),
        (r"\bINACTIVE\b", "inativo"),
        (r"\bACTIVE\b", "ativo"),
        (r"\bBLOCKED\b", "bloqueada"),
        (r"\bPENDING\b", "pendente"),
        (r"\bERROR\b", "erro"),
        (r"\bWAITING\b", "aguardando"),
        (r"\bPROCESSED\b", "processada"),
        (r"\bCOMPLETED\b", "concluída"),
        (r"\bINSTALLATION\b", "instalação"),
        (r"\bMAINTENANCE\b", "manutenção"),
        (r"\bCANCELLATION\b", "cancelamento"),
        (r"\bOrdem de Servico\b", "Ordem de Serviço"),
        (r"\bServico\b", "Serviço"),
    ]

    result = text
    for pattern, replacement in replacements:
        result = re.sub(
            pattern,
            replacement,
            result,
            flags=re.IGNORECASE,
        )

    return result


def extract_service_order_id(message: str) -> int | None:
    return extract_os_id(message)



def _service_type_label(value: str | None) -> str:
    labels = {
        "INSTALLATION": "instalação",
        "MAINTENANCE": "manutenção",
        "CANCELLATION": "cancelamento",
    }
    return labels.get(str(value or "").upper(), str(value or "").lower())


def extract_requested_service_order_type(
    message: str,
) -> str | None:
    return detect_requested_service_order_type(message)



def detect_direct_intent(message: str) -> str | None:
    return detect_intent(message)



def is_fleetops_scope(
    message: str,
    direct_intent: str | None = None,
) -> bool:
    return check_fleetops_scope(
        message,
        direct_intent,
    )



async def scope_guard(
    state: AgentState,
) -> dict:

    allowed = is_fleetops_scope(
        state.get(
            "question",
            "",
        ),
        state.get(
            "direct_intent"
        ),
    )

    return {
        "out_of_scope":
            not allowed
    }


def route_after_scope_guard(
    state: AgentState,
) -> str:

    route = (
        "out_of_scope"
        if state.get(
            "out_of_scope",
            False,
        )
        else "diagnostic"
    )

    log_event(
        "agent_scope_decision",
        trace_id=
            state.get(
                "trace_id"
            ),
        thread_id=
            state.get(
                "thread_id"
            ),
        out_of_scope=
            state.get(
                "out_of_scope",
                False,
            ),
        next_node=
            route,
    )

    return route


async def out_of_scope_answer(
    state: AgentState,
) -> dict:

    answer = (
        "Posso ajudar com assuntos do FleetOps, "
        "como Ordens de Serviço, contratos, placas, "
        "filas de processamento e diagnósticos operacionais. "
        "Essa pergunta está fora desse escopo."
    )

    log_event(
        "out_of_scope_answer_completed",
        trace_id=
            state.get(
                "trace_id"
            ),
        question=
            state.get(
                "question"
            ),
    )

    return {
        "answer":
            answer,

        "response_mode":
            "OUT_OF_SCOPE",

        "knowledge_sources":
            [],

        "degraded":
            False,

        "warnings":
            [],
    }


def ensure_mcp_success(result, tool_name: str):
    is_error = (
        getattr(result, "isError", False)
        or getattr(result, "is_error", False)
    )

    if is_error:
        raise RuntimeError(
            f"A tool {tool_name} retornou erro."
        )


def mcp_result_to_text(result) -> str:
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

    return ""


def build_diagnostic_fallback(state: AgentState) -> str:
    try:
        diagnostic = json.loads(state["diagnostic"])
    except Exception:
        return (
            "O diagnóstico foi obtido, "
            "mas não foi possível gerar "
            "a explicação neste momento."
        )

    service_order_id = state.get("service_order_id")
    diagnostic_status = diagnostic.get("diagnostic_status")
    problems = diagnostic.get("problems") or []

    if diagnostic_status == "BLOCKED":
        if problems:
            translated_problems = [
                normalize_user_answer(str(problem))
                for problem in problems
            ]
            problem_text = " ".join(translated_problems)

            return (
                f"A OS {service_order_id} está bloqueada. "
                f"{problem_text}"
            )

        return f"A OS {service_order_id} está bloqueada."

    translated_status = normalize_user_answer(
        str(diagnostic_status)
    )

    return (
        f"A OS {service_order_id} está com diagnóstico "
        f"{translated_status}."
    )


def route_after_diagnostic(state: AgentState) -> str:
    diagnostic = json.loads(state["diagnostic"])
    diagnostic_status = diagnostic.get("diagnostic_status")
    direct_intent = state.get("direct_intent")

    if direct_intent == "why_blocked":
        route = (
            "knowledge"
            if diagnostic_status == "BLOCKED"
            else "direct_answer"
        )
    elif direct_intent:
        route = "direct_answer"
    elif diagnostic_status == "BLOCKED":
        route = "knowledge"
    else:
        route = "answer"

    log_event(
        "agent_route_decision",
        trace_id=state.get("trace_id"),
        service_order_id=state.get("service_order_id"),
        diagnostic_status=diagnostic_status,
        direct_intent=direct_intent,
        next_node=route,
    )

    return route


async def get_diagnostic(state: AgentState) -> dict:
    trace_id = state.get("trace_id")
    start = time.perf_counter()

    log_event(
        "node_started",
        trace_id=trace_id,
        node="diagnostic",
        service_order_id=state["service_order_id"],
    )

    try:
        if FORCE_DIAGNOSTIC_ERROR:
            raise RuntimeError(
                "Falha simulada no diagnostico."
            )

        tool_start = time.perf_counter()

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_service_order_diagnostic",
                {
                    "service_order_id":
                        state["service_order_id"]
                },
            )

        tool_duration = round(
            (time.perf_counter() - tool_start) * 1000,
            2,
        )

        ensure_mcp_success(
            result,
            "get_service_order_diagnostic",
        )

        log_event(
            "mcp_tool_completed",
            trace_id=trace_id,
            tool="get_service_order_diagnostic",
            duration_ms=tool_duration,
        )

        diagnostic = mcp_result_to_text(result)

        try:
            diagnostic_data = json.loads(diagnostic)
        except json.JSONDecodeError as exc:
            raise AgentDependencyError(
                "O diagnostico retornou um formato invalido."
            ) from exc

        if (
            diagnostic_data.get("error")
            == "SERVICE_ORDER_NOT_FOUND"
        ):
            raise ServiceOrderNotFoundError(
                f"OS {state['service_order_id']} nao encontrada."
            )

        total_duration = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        log_event(
            "node_completed",
            trace_id=trace_id,
            node="diagnostic",
            duration_ms=total_duration,
        )

        return {
            "diagnostic": diagnostic,
            "knowledge": "",
        }

    except ServiceOrderNotFoundError:
        raise

    except AgentDependencyError:
        raise

    except Exception as exc:
        log_event(
            "dependency_failed",
            trace_id=trace_id,
            dependency="mcp:get_service_order_diagnostic",
            error=str(exc),
        )

        raise AgentDependencyError(
            "Nao foi possivel consultar "
            "os dados operacionais da OS."
        ) from exc


async def direct_answer(state: AgentState) -> dict:
    trace_id = state.get("trace_id")
    start = time.perf_counter()

    diagnostic = json.loads(state["diagnostic"])
    service_order = diagnostic.get("service_order") or {}
    contract = diagnostic.get("contract") or {}
    queue = diagnostic.get("queue") or {}

    service_order_id = state["service_order_id"]
    intent = state.get("direct_intent")
    question = state.get("question", "")

    log_event(
        "node_started",
        trace_id=trace_id,
        node="direct_answer",
        direct_intent=intent,
    )

    premise_answer = build_premise_response(
        intent=intent,
        diagnostic=diagnostic,
        service_order_id=service_order_id,
    )

    if premise_answer is not None:
        answer = premise_answer
    elif intent == "contract_number":
        contract_id = contract.get("id")
        if contract_id is None:
            answer = f"A OS {service_order_id} não possui contrato associado."
        else:
            answer = f"O contrato da OS {service_order_id} é o {contract_id}."

    elif intent == "contract_status":
        contract_id = contract.get("id")
        contract_status = contract.get("status")
        if contract_id is None:
            answer = f"A OS {service_order_id} não possui contrato associado."
        else:
            translated_status = normalize_user_answer(str(contract_status))
            answer = f"O contrato {contract_id} está {translated_status}."

    elif intent == "vehicle_plate":
        plate = service_order.get("vehicle_plate")
        if plate:
            answer = f"A placa da OS {service_order_id} é {plate}."
        else:
            answer = f"A OS {service_order_id} não possui placa informada."

    elif intent == "service_order_type":
        service_type = service_order.get("type")

        if not service_type:
            answer = f"A OS {service_order_id} não possui tipo informado."
        else:
            type_label = _service_type_label(service_type)
            requested_type = extract_requested_service_order_type(question)

            if requested_type is None:
                answer = f"A OS {service_order_id} é do tipo {type_label}."
            elif str(service_type).upper() == requested_type:
                answer = f"Sim. A OS {service_order_id} é do tipo {type_label}."
            else:
                requested_label = _service_type_label(requested_type)
                answer = (
                    f"Não. A OS {service_order_id} é do tipo {type_label}, "
                    f"não {requested_label}."
                )

    elif intent == "service_order_summary":
        operational_status = service_order.get("status")
        service_type = service_order.get("type")
        plate = service_order.get("vehicle_plate")
        contract_id = contract.get("id")
        contract_status = contract.get("status")
        queue_status = queue.get("status") if queue else None
        diagnostic_status = diagnostic.get("diagnostic_status")

        operational_label = normalize_user_answer(str(operational_status))
        type_label = _service_type_label(service_type)
        diagnostic_label = normalize_user_answer(str(diagnostic_status))

        parts = [
            (
                f"A OS {service_order_id} está com status operacional "
                f"{operational_label}, é do tipo {type_label}"
                + (f" e está vinculada à placa {plate}" if plate else "")
                + "."
            )
        ]

        if contract_id is not None:
            contract_label = normalize_user_answer(str(contract_status))
            parts.append(f"O contrato {contract_id} está {contract_label}.")

        if queue_status:
            queue_label = normalize_user_answer(str(queue_status))
            parts.append(f"A fila está {queue_label}.")
        else:
            parts.append("Não há fila de processamento.")

        parts.append(f"O diagnóstico da OS é {diagnostic_label}.")
        answer = " ".join(parts)

    elif intent == "service_order_status":
        operational_status = service_order.get("status")
        diagnostic_status = diagnostic.get("diagnostic_status")
        operational_label = normalize_user_answer(str(operational_status))
        diagnostic_label = normalize_user_answer(str(diagnostic_status))
        answer = (
            f"A OS {service_order_id} está com status operacional "
            f"{operational_label} e diagnóstico {diagnostic_label}."
        )

    elif intent == "queue_status":
        if not queue:
            answer = f"A OS {service_order_id} não possui fila de processamento."
        else:
            queue_status = normalize_user_answer(str(queue.get("status")))
            answer = (
                f"A fila da OS {service_order_id} está com status "
                f"{queue_status}."
            )

    elif intent == "queue_error":
        if not queue:
            answer = f"A OS {service_order_id} não possui fila de processamento."
        else:
            queue_error = queue.get("error")
            if queue_error:
                translated_error = normalize_user_answer(str(queue_error))
                answer = (
                    f"O erro da fila da OS {service_order_id} é: "
                    f"{translated_error}."
                )
            else:
                answer = (
                    f"A fila da OS {service_order_id} "
                    "não possui erro registrado."
                )

    else:
        answer = "Não foi possível identificar a informação solicitada."

    duration = round((time.perf_counter() - start) * 1000, 2)

    log_event(
        "direct_answer_completed",
        trace_id=trace_id,
        service_order_id=service_order_id,
        direct_intent=intent,
        duration_ms=duration,
    )

    log_event(
        "node_completed",
        trace_id=trace_id,
        node="direct_answer",
        duration_ms=duration,
    )

    return {
        "answer": answer,
        "response_mode": "DIRECT",
    }


async def get_knowledge(state: AgentState) -> dict:
    trace_id = state.get("trace_id")
    start = time.perf_counter()

    log_event(
        "node_started",
        trace_id=trace_id,
        node="knowledge",
        service_order_id=state["service_order_id"],
    )

    try:
        if FORCE_RAG_ERROR:
            raise RuntimeError(
                "Falha simulada no RAG."
            )

        tool_start = time.perf_counter()

        async with Client(mcp) as client:
            result = await client.call_tool(
                "search_knowledge",
                {
                    "query": state["diagnostic"],
                    "limit": 3,
                    "trace_id": trace_id,
                },
            )

        tool_duration = round(
            (time.perf_counter() - tool_start) * 1000,
            2,
        )

        ensure_mcp_success(
            result,
            "search_knowledge",
        )

        log_event(
            "mcp_tool_completed",
            trace_id=trace_id,
            tool="search_knowledge",
            duration_ms=tool_duration,
        )

        knowledge = mcp_result_to_text(result)

        total_duration = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        log_event(
            "node_completed",
            trace_id=trace_id,
            node="knowledge",
            duration_ms=total_duration,
        )

        knowledge_sources = []

        try:
            parsed_knowledge = json.loads(
                knowledge
            )

            if isinstance(
                parsed_knowledge,
                list,
            ):
                for item in parsed_knowledge:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    knowledge_sources.append(
                        {
                            "source":
                                item.get(
                                    "source"
                                ),

                            "similarity":
                                item.get(
                                    "similarity"
                                ),

                            "content":
                                item.get(
                                    "content"
                                ),
                        }
                    )

        except json.JSONDecodeError:

            knowledge_sources = []


        return {
            "knowledge":
                knowledge,

            "knowledge_sources":
                knowledge_sources,
        }

    except Exception as exc:
        warning = (
            "A base de conhecimento "
            "não estava disponível nesta consulta."
        )

        log_event(
            "dependency_failed",
            trace_id=trace_id,
            dependency="mcp:search_knowledge",
            error=str(exc),
            fallback="continue_without_rag",
        )

        return {
            "knowledge":
                "",

            "knowledge_sources":
                [],

            "degraded":
                True,

            "warnings":
                [warning],
        }


async def generate_answer(state: AgentState) -> dict:
    trace_id = state.get("trace_id")
    start = time.perf_counter()

    log_event(
        "node_started",
        trace_id=trace_id,
        node="answer",
        model=MODEL,
    )

    if state.get("degraded", False):
        fallback_answer = build_diagnostic_fallback(
            state
        )

        log_event(
            "degraded_answer_completed",
            trace_id=trace_id,
            reason="dependency_unavailable",
            strategy="deterministic_answer",
        )

        return {
            "answer": fallback_answer,
            "degraded": True,
            "warnings": state.get(
                "warnings",
                [],
            ),
            "response_mode": "DEGRADED",
        }

    question = state.get(
        "question",
        "Explique a situacao desta OS.",
    )

    knowledge = (
        state.get("knowledge")
        or "Nenhuma regra adicional está disponível."
    )

    diagnostic_for_llm = normalize_user_answer(
        state["diagnostic"]
    )

    knowledge_for_llm = normalize_user_answer(
        knowledge
    )

    try:
        if FORCE_LLM_ERROR:
            raise RuntimeError(
                "Falha simulada no LLM."
            )

        llm_start = time.perf_counter()

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Voce e um assistente de diagnostico operacional. "
                        "Responda sempre em portugues. "
                        "Use somente os fatos e regras fornecidos. "
                        "Nao invente informacoes. "
                        "Nao repita a mesma informacao. "
                        "Nao use listas. "
                        "Responda em no maximo 3 frases e 70 palavras. "
                        "Explique de forma simples e objetiva."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"PERGUNTA:\n{question}\n\n"
                        f"OS:\n{state['service_order_id']}\n\n"
                        f"DIAGNOSTICO:\n{diagnostic_for_llm}\n\n"
                        f"CONHECIMENTO:\n{knowledge_for_llm}"
                    ),
                },
            ],
            options={
                "temperature": 0,
                "num_predict": 120,
            },
            keep_alive="30m",
        )

        llm_duration = round(
            (time.perf_counter() - llm_start) * 1000,
            2,
        )

        log_event(
            "ollama_chat_metrics",
            trace_id=trace_id,
            model=MODEL,
            total_ms=ns_to_ms(
                getattr(
                    response,
                    "total_duration",
                    0,
                )
            ),
            load_ms=ns_to_ms(
                getattr(
                    response,
                    "load_duration",
                    0,
                )
            ),
            prompt_eval_ms=ns_to_ms(
                getattr(
                    response,
                    "prompt_eval_duration",
                    0,
                )
            ),
            generation_ms=ns_to_ms(
                getattr(
                    response,
                    "eval_duration",
                    0,
                )
            ),
            prompt_tokens=getattr(
                response,
                "prompt_eval_count",
                0,
            ),
            output_tokens=getattr(
                response,
                "eval_count",
                0,
            ),
        )

        log_event(
            "llm_completed",
            trace_id=trace_id,
            model=MODEL,
            duration_ms=llm_duration,
        )

        total_duration = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        log_event(
            "node_completed",
            trace_id=trace_id,
            node="answer",
            duration_ms=total_duration,
        )

        answer = normalize_user_answer(
            response.message.content
        )

        return {
            "answer": answer,
            "response_mode": "AI",
        }

    except Exception as exc:
        warning = (
            "O modelo de linguagem "
            "não estava disponível. "
            "A resposta foi gerada "
            "somente com os dados operacionais."
        )

        existing_warnings = list(
            state.get(
                "warnings",
                [],
            )
        )

        existing_warnings.append(
            warning
        )

        fallback_answer = build_diagnostic_fallback(
            state
        )

        log_event(
            "dependency_failed",
            trace_id=trace_id,
            dependency="ollama:chat",
            model=MODEL,
            error=str(exc),
            fallback="deterministic_answer",
        )

        return {
            "answer": fallback_answer,
            "degraded": True,
            "warnings": existing_warnings,
            "response_mode": "DEGRADED",
        }


def build_agent_graph(checkpointer):
    builder = StateGraph(
        AgentState
    )

    builder.add_node(
        "scope_guard",
        scope_guard,
    )

    builder.add_node(
        "out_of_scope",
        out_of_scope_answer,
    )

    builder.add_node(
        "diagnostic",
        get_diagnostic,
    )

    builder.add_node(
        "direct_answer",
        direct_answer,
    )

    builder.add_node(
        "knowledge",
        get_knowledge,
    )

    builder.add_node(
        "answer",
        generate_answer,
    )

    builder.add_edge(
        START,
        "scope_guard",
    )

    builder.add_conditional_edges(
        "scope_guard",
        route_after_scope_guard,
        {
            "out_of_scope": "out_of_scope",
            "diagnostic": "diagnostic",
        },
    )

    builder.add_edge(
        "out_of_scope",
        END,
    )

    builder.add_conditional_edges(
        "diagnostic",
        route_after_diagnostic,
        {
            "direct_answer": "direct_answer",
            "knowledge": "knowledge",
            "answer": "answer",
        },
    )

    builder.add_edge(
        "direct_answer",
        END,
    )

    builder.add_edge(
        "knowledge",
        "answer",
    )

    builder.add_edge(
        "answer",
        END,
    )

    return builder.compile(
        checkpointer=checkpointer
    )


async def run_agent(
    graph,
    thread_id: str,
    message: str,
    trace_id: str,
) -> dict:

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    service_order_id = extract_service_order_id(
        message
    )

    direct_intent = detect_direct_intent(
        message
    )

    log_event(
        "intent_detected",
        trace_id=trace_id,
        thread_id=thread_id,
        direct_intent=direct_intent,
    )

    input_state = {
        "trace_id":
            trace_id,

        "thread_id":
            thread_id,

        "question":
            message,

        "direct_intent":
            direct_intent,

        "degraded":
            False,

        "warnings":
            [],

        "knowledge_sources":
            [],

        "out_of_scope":
            False,
    }

    if service_order_id is not None:
        input_state[
            "service_order_id"
        ] = service_order_id

    else:
        snapshot = await graph.aget_state(
            config
        )

        current_state = (
            snapshot.values
            if snapshot
            else {}
        )

        remembered_service_order_id = (
            current_state.get(
                "service_order_id"
            )
        )

        if not remembered_service_order_id:
            raise ValueError(
                "Nenhuma OS foi informada "
                "e esta conversa ainda nao "
                "possui uma OS em contexto."
            )

    return await graph.ainvoke(
        input_state,
        config=config,
    )
