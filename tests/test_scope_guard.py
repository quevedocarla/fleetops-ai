import asyncio

import app.services.agent_service as agent_service


def test_math_is_out_of_scope():

    assert (
        agent_service.is_fleetops_scope(
            "qual a soma de 1 + 2"
        )
        is False
    )


def test_recipe_is_out_of_scope():

    assert (
        agent_service.is_fleetops_scope(
            "como fazer bolo de cenoura?"
        )
        is False
    )


def test_queue_followup_is_in_scope():

    intent = (
        agent_service.detect_direct_intent(
            "qual o status da fila?"
        )
    )

    assert intent == "queue_status"

    assert (
        agent_service.is_fleetops_scope(
            "qual o status da fila?",
            intent,
        )
        is True
    )


def test_blocked_followup_is_in_scope():

    assert (
        agent_service.is_fleetops_scope(
            "por que ela está bloqueada?"
        )
        is True
    )


def test_explicit_os_is_in_scope():

    assert (
        agent_service.is_fleetops_scope(
            "analise a OS 10235"
        )
        is True
    )


def test_out_of_scope_answer_is_deterministic(
    monkeypatch,
):

    def fail_if_llm_called(*args, **kwargs):
        raise AssertionError(
            "LLM nao deveria ser chamado."
        )

    monkeypatch.setattr(
        agent_service,
        "chat",
        fail_if_llm_called,
    )

    result = asyncio.run(
        agent_service.out_of_scope_answer(
            {
                "trace_id":
                    "scope-test-001",

                "question":
                    "como fazer bolo de cenoura?",
            }
        )
    )

    assert (
        result["response_mode"]
        == "OUT_OF_SCOPE"
    )

    assert (
        result["knowledge_sources"]
        == []
    )

    assert result["degraded"] is False

    assert (
        "fora desse escopo"
        in result["answer"].lower()
    )
