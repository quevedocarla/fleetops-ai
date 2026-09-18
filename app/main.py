import os
import time
import uuid

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Request,
)

from fastapi.responses import (
    FileResponse,
)

from fastapi.staticfiles import (
    StaticFiles,
)

from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)

from app.api.agent import (
    router as agent_router,
)

from app.api.service_orders import (
    router as service_orders_router,
)

from app.core.observability import (
    log_event,
)

from app.services.agent_service import (
    build_agent_graph,
)


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL nao encontrada."
    )


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


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
)


STATIC_DIR = (
    BASE_DIR
    / "static"
)


INDEX_FILE = (
    STATIC_DIR
    / "index.html"
)


if not STATIC_DIR.exists():
    raise RuntimeError(
        f"Pasta static nao encontrada: {STATIC_DIR}"
    )


if not INDEX_FILE.exists():
    raise RuntimeError(
        f"index.html nao encontrado: {INDEX_FILE}"
    )


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    log_event(
        "application_starting"
    )


    async with AsyncPostgresSaver.from_conn_string(
        CHECKPOINT_DB_URL
    ) as checkpointer:

        await checkpointer.setup()


        app.state.agent_graph = (
            build_agent_graph(
                checkpointer
            )
        )


        log_event(
            "agent_graph_ready"
        )


        yield


    log_event(
        "application_shutdown"
    )


app = FastAPI(
    title="FleetOps AI",
    version="1.0.0",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(
        directory=str(
            STATIC_DIR
        )
    ),
    name="static",
)


@app.middleware(
    "http"
)
async def observability_middleware(
    request: Request,
    call_next,
):

    trace_id = (
        request.headers.get(
            "X-Trace-ID"
        )
        or
        str(
            uuid.uuid4()
        )
    )


    request.state.trace_id = (
        trace_id
    )


    start_time = (
        time.perf_counter()
    )


    log_event(
        "http_request_started",
        trace_id=trace_id,
        method=request.method,
        path=request.url.path,
    )


    try:
        response = await call_next(
            request
        )

    except Exception as exc:

        duration_ms = round(
            (
                time.perf_counter()
                -
                start_time
            )
            * 1000,
            2,
        )


        log_event(
            "http_request_failed",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            error=str(exc),
        )


        raise


    duration_ms = round(
        (
            time.perf_counter()
            -
            start_time
        )
        * 1000,
        2,
    )


    response.headers[
        "X-Trace-ID"
    ] = trace_id


    log_event(
        "http_request_completed",
        trace_id=trace_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )


    return response


app.include_router(
    service_orders_router
)


app.include_router(
    agent_router
)


@app.get(
    "/",
    include_in_schema=False,
)
async def frontend():

    return FileResponse(
        path=str(
            INDEX_FILE
        ),
        media_type="text/html",
    )


@app.get(
    "/health",
    tags=[
        "Health"
    ],
)
def health():

    return {
        "status": "ok",
        "service": "fleetops-ai",
    }
