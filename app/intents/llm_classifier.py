import json
import os
import time
from dataclasses import dataclass

from ollama import chat

from app.core.observability import log_event
from app.intents.models import (
    CONTRACT_NUMBER,
    CONTRACT_STATUS,
    IS_BLOCKED,
    QUEUE_ERROR,
    QUEUE_STATUS,
    SERVICE_ORDER_STATUS,
    SERVICE_ORDER_SUMMARY,
    SERVICE_ORDER_TYPE,
    VEHICLE_PLATE,
    WHY_BLOCKED,
)


INTENT_MODEL = os.getenv(
    "FLEETOPS_INTENT_MODEL",
    "qwen2.5:1.5b-instruct",
)

MIN_CONFIDENCE = float(
    os.getenv(
        "FLEETOPS_INTENT_MIN_CONFIDENCE",
        "0.70",
    )
)

DIRECT_INTENTS = {
    CONTRACT_NUMBER,
    CONTRACT_STATUS,
    VEHICLE_PLATE,
    SERVICE_ORDER_STATUS,
    SERVICE_ORDER_TYPE,
    SERVICE_ORDER_SUMMARY,
    QUEUE_STATUS,
    QUEUE_ERROR,
    IS_BLOCKED,
    WHY_BLOCKED,
}

SPECIAL_INTENTS = {
    "analytical",
    "out_of_scope",
}

ALLOWED_INTENTS = DIRECT_INTENTS | SPECIAL_INTENTS


@dataclass(frozen=True)
class IntentClassification:
    intent: str | None
    confidence: float
    out_of_scope: bool = False


def _parse_json_object(text: str) -> dict:
    content = (text or "").strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise

        parsed = json.loads(
            content[start:end + 1]
        )

    if not isinstance(parsed, dict):
        raise ValueError(
            "Classificação de intenção não retornou objeto JSON."
        )

    return parsed


def _normalize_confidence(value) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0

    return max(
        0.0,
        min(confidence, 1.0),
    )


def classify_intent_with_llm(
    message: str,
    *,
    trace_id: str | None = None,
) -> IntentClassification:
    start = time.perf_counter()

    response = chat(
        model=INTENT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Voce classifica perguntas de um sistema operacional "
                    "de gestao de Ordens de Servico. "
                    "Nao responda a pergunta. "
                    "Retorne somente JSON valido. "
                    "Escolha exatamente uma intencao entre: "
                    "contract_number, contract_status, vehicle_plate, "
                    "service_order_status, service_order_type, "
                    "service_order_summary, queue_status, queue_error, "
                    "is_blocked, why_blocked, analytical, out_of_scope. "
                    "Use service_order_summary quando o usuario quer saber "
                    "de forma geral como esta a OS. "
                    "Use service_order_status quando quer somente situacao/status. "
                    "Use queue_status para situacao da fila. "
                    "Use queue_error para erro da fila/processamento. "
                    "Use why_blocked quando pergunta a causa de bloqueio. "
                    "Use is_blocked quando pergunta se esta bloqueada. "
                    "Use analytical quando a pergunta exige explicacao operacional "
                    "mas nao se encaixa nas intencoes diretas. "
                    "Use out_of_scope somente quando o assunto nao pertence a "
                    "Ordens de Servico, contratos, veiculos, filas ou diagnosticos. "
                    "Formato obrigatorio: "
                    "{\"intent\":\"nome\",\"confidence\":0.0}"
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        format="json",
        options={
            "temperature": 0,
            "num_predict": 50,
        },
        keep_alive="30m",
    )

    parsed = _parse_json_object(
        response.message.content
    )

    raw_intent = str(
        parsed.get("intent") or ""
    ).strip().lower()

    confidence = _normalize_confidence(
        parsed.get("confidence")
    )

    duration_ms = round(
        (time.perf_counter() - start) * 1000,
        2,
    )

    log_event(
        "intent_llm_classified",
        trace_id=trace_id,
        model=INTENT_MODEL,
        classified_intent=raw_intent or None,
        confidence=confidence,
        duration_ms=duration_ms,
    )

    if raw_intent not in ALLOWED_INTENTS:
        return IntentClassification(
            intent=None,
            confidence=confidence,
        )

    if confidence < MIN_CONFIDENCE:
        return IntentClassification(
            intent=None,
            confidence=confidence,
        )

    if raw_intent == "out_of_scope":
        return IntentClassification(
            intent=None,
            confidence=confidence,
            out_of_scope=True,
        )

    if raw_intent == "analytical":
        return IntentClassification(
            intent=None,
            confidence=confidence,
        )

    return IntentClassification(
        intent=raw_intent,
        confidence=confidence,
    )
