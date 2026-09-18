import json
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


logger = logging.getLogger(
    "fleetops"
)


def log_event(
    event: str,
    **fields,
):
    """
    Gera logs estruturados em JSON.

    Exemplo:

    {
        "event": "http_request",
        "trace_id": "...",
        "duration_ms": 123
    }
    """

    payload = {
        "event": event,
        **fields,
    }

    logger.info(
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )