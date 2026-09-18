import asyncio
import json

import app.services.agent_service as agent_service


DIAGNOSTIC_10235 = json.dumps(
    {
        "service_order": {
            "id": 10235,
            "status": "PENDING",
            "type": "INSTALLATION",
            "vehicle_plate": "DEF4G56",
        },
        "contract": {
            "id": 2002,
            "status": "INACTIVE",
        },
        "queue": {
            "status": "ERROR",
            "error": "Contract is inactive",
        },
        "diagnostic_status": "BLOCKED",
        "problems": ["Contrato 2002 esta inativo."],
    }
)

DIAGNOSTIC_10236 = json.dumps(
    {
        "service_order": {
            "id": 10236,
            "status": "COMPLETED",
            "type": "MAINTENANCE",
            "vehicle_plate": "GHI7J89",
        },
        "contract": {
            "id": 2003,
            "status": "ACTIVE",
        },
        "queue": {
            "status": "PROCESSED",
            "error": None,
        },
        "diagnostic_status": "OK",
        "problems": [],
    }
)


def run_direct(*, service_order_id, question, diagnostic):
    intent = agent_service.detect_direct_intent(question)
    result = asyncio.run(
        agent_service.direct_answer(
            {
                "trace_id": "pytest-chat-regression",
                "service_order_id": service_order_id,
                "question": question,
                "direct_intent": intent,
                "diagnostic": diagnostic,
            }
        )
    )
    return intent, result


def test_short_plate_followup_is_direct():
    assert agent_service.detect_direct_intent("a placa") == "vehicle_plate"


def test_short_plate_followup_returns_real_plate():
    intent, result = run_direct(
        service_order_id=10235,
        question="a placa",
        diagnostic=DIAGNOSTIC_10235,
    )
    assert intent == "vehicle_plate"
    assert result["response_mode"] == "DIRECT"
    assert result["answer"] == "A placa da OS 10235 é DEF4G56."


def test_maintenance_confirmation_detected_as_type_intent():
    assert (
        agent_service.detect_direct_intent("esta em manutenção?")
        == "service_order_type"
    )


def test_installation_os_does_not_claim_maintenance():
    intent, result = run_direct(
        service_order_id=10235,
        question="esta em manutenção?",
        diagnostic=DIAGNOSTIC_10235,
    )
    assert intent == "service_order_type"
    assert result["response_mode"] == "DIRECT"
    assert result["answer"].startswith("Não.")
    assert "instalação" in result["answer"]
    assert "não manutenção" in result["answer"]


def test_maintenance_os_confirms_maintenance():
    _, result = run_direct(
        service_order_id=10236,
        question="é manutenção?",
        diagnostic=DIAGNOSTIC_10236,
    )
    assert result["answer"] == "Sim. A OS 10236 é do tipo manutenção."


def test_bare_service_order_is_summary_intent():
    assert (
        agent_service.detect_direct_intent("a OS 10236")
        == "service_order_summary"
    )


def test_service_order_summary_is_deterministic():
    intent, result = run_direct(
        service_order_id=10236,
        question="a OS 10236",
        diagnostic=DIAGNOSTIC_10236,
    )
    assert intent == "service_order_summary"
    assert result["response_mode"] == "DIRECT"
    answer = result["answer"]
    assert "10236" in answer
    assert "concluída" in answer
    assert "manutenção" in answer
    assert "GHI7J89" in answer
    assert "2003" in answer
    assert "ativo" in answer
    assert "processada" in answer
    assert "OK" in answer


def test_natural_linked_contract_question_is_direct():
    assert (
        agent_service.detect_direct_intent(
            "qual contrato esta vinculado a essa os"
        )
        == "contract_number"
    )


def test_natural_linked_contract_question_returns_contract():
    intent, result = run_direct(
        service_order_id=10235,
        question="qual contrato esta vinculado a essa os",
        diagnostic=DIAGNOSTIC_10235,
    )

    assert intent == "contract_number"
    assert result["response_mode"] == "DIRECT"
    assert result["answer"] == "O contrato da OS 10235 é o 2002."


def test_and_plate_followup_is_direct():
    assert (
        agent_service.detect_direct_intent("e a placa")
        == "vehicle_plate"
    )


def test_and_plate_followup_returns_real_plate():
    intent, result = run_direct(
        service_order_id=10235,
        question="e a placa",
        diagnostic=DIAGNOSTIC_10235,
    )

    assert intent == "vehicle_plate"
    assert result["response_mode"] == "DIRECT"
    assert result["answer"] == "A placa da OS 10235 é DEF4G56."
