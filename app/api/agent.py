import json

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from app.core.observability import (
    log_event,
)

from app.schemas.agent_chat import (
    AgentChatRequest,
    AgentChatResponse,
)

from app.services.agent_service import (
    AgentDependencyError,
    ServiceOrderNotFoundError,
    run_agent,
)


router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    responses={
        400: {
            "description":
                "Mensagem sem OS e thread sem contexto."
        },
        404: {
            "description":
                "Ordem de Servico nao encontrada."
        },
        500: {
            "description":
                "Erro inesperado no agente."
        },
        503: {
            "description":
                "Dependencia essencial indisponivel."
        },
    },
)
async def agent_chat(
    payload: AgentChatRequest,
    request: Request,
):

    trace_id = (
        request.state.trace_id
    )

    log_event(
        "agent_chat_started",
        trace_id=trace_id,
        thread_id=payload.thread_id,
        message=payload.message,
    )

    graph = getattr(
        request.app.state,
        "agent_graph",
        None,
    )

    if graph is None:
        raise HTTPException(
            status_code=503,
            detail={
                "message":
                    "Agent Graph nao esta inicializado.",
                "trace_id":
                    trace_id,
            },
        )

    try:
        result = await run_agent(
            graph=graph,
            thread_id=payload.thread_id,
            message=payload.message,
            trace_id=trace_id,
        )

    except ValueError as exc:
        log_event(
            "agent_chat_validation_error",
            trace_id=trace_id,
            thread_id=payload.thread_id,
            error=str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "trace_id": trace_id,
            },
        ) from exc

    except ServiceOrderNotFoundError as exc:
        log_event(
            "service_order_not_found",
            trace_id=trace_id,
            thread_id=payload.thread_id,
            error=str(exc),
        )

        raise HTTPException(
            status_code=404,
            detail={
                "message": str(exc),
                "trace_id": trace_id,
            },
        ) from exc

    except AgentDependencyError as exc:
        log_event(
            "agent_dependency_error",
            trace_id=trace_id,
            thread_id=payload.thread_id,
            error=str(exc),
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message": str(exc),
                "trace_id": trace_id,
            },
        ) from exc

    except Exception as exc:
        log_event(
            "agent_unexpected_error",
            trace_id=trace_id,
            thread_id=payload.thread_id,
            error=str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "Ocorreu um erro inesperado "
                    "ao processar a solicitacao.",
                "trace_id":
                    trace_id,
            },
        ) from exc

    diagnostic_status = None
    diagnostic_text = result.get("diagnostic")

    if diagnostic_text:
        try:
            diagnostic = json.loads(
                diagnostic_text
            )
            diagnostic_status = (
                diagnostic.get(
                    "diagnostic_status"
                )
            )
        except json.JSONDecodeError:
            diagnostic_status = None

    degraded = bool(
        result.get(
            "degraded",
            False,
        )
    )

    warnings = (
        result.get(
            "warnings",
            [],
        )
        or []
    )

    response_mode = (
        result.get(
            "response_mode",
            "AI",
        )
    )


    sources = (
        result.get(
            "knowledge_sources",
            [],
        )
        or []
    )

    log_event(
        "agent_chat_completed",
        trace_id=trace_id,
        thread_id=payload.thread_id,
        service_order_id=result[
            "service_order_id"
        ],
        diagnostic_status=diagnostic_status,
        degraded=degraded,
        warnings_count=len(warnings),
        response_mode=
            response_mode,

        sources=
            sources,
    )

    return AgentChatResponse(
        trace_id=trace_id,
        thread_id=payload.thread_id,
        service_order_id=result[
            "service_order_id"
        ],
        status=diagnostic_status,
        answer=result["answer"],
        degraded=degraded,
        warnings=warnings,
        response_mode=
            response_mode,

        sources=
            sources,
    )
