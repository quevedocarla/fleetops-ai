import asyncio
import json

import app.services.agent_service as agent_service


DIAGNOSTIC_10236 = json.dumps(
    {
        "service_order": {
            "id": 10236,
            "status": "COMPLETED",
            "type": "MAINTENANCE",
            "vehicle_plate": "GHI7J89",
        },
        "contract": {"id": 2003, "status": "ACTIVE"},
        "queue": {"status": "PROCESSED", "error": None},
        "diagnostic_status": "OK",
        "problems": [],
    }
)


def test_order_word_extracts_service_order_id():
    assert agent_service.extract_service_order_id(
        "a ordem 10236 como esta?"
    ) == 10236


def test_order_summary_natural_phrase_is_direct():
    assert agent_service.detect_direct_intent(
        "a ordem 10236 como esta?"
    ) == "service_order_summary"


def test_order_phrase_is_in_scope():
    assert agent_service.is_fleetops_scope(
        "a ordem 10236 como esta?"
    ) is True


def test_status_typo_is_direct():
    assert agent_service.detect_direct_intent(
        "esta pendente o sstatus"
    ) == "service_order_status"


def test_why_blocked_intent_is_detected():
    assert agent_service.detect_direct_intent(
        "Por que a OS 10236 está bloqueada?"
    ) == "why_blocked"


def test_false_blocked_premise_is_corrected():
    result = asyncio.run(
        agent_service.direct_answer(
            {
                "trace_id": "premise-regression",
                "service_order_id": 10236,
                "question": "Por que a OS 10236 está bloqueada?",
                "direct_intent": "why_blocked",
                "diagnostic": DIAGNOSTIC_10236,
            }
        )
    )

    assert result["response_mode"] == "DIRECT"
    assert result["answer"] == (
        "A OS 10236 não está bloqueada. "
        "Ela está concluída."
    )
