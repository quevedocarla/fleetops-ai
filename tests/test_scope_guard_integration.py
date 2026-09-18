import uuid

import httpx
import pytest


BASE_URL = "http://127.0.0.1:8000"


def create_thread():

    return (
        "pytest-scope-"
        +
        str(
            uuid.uuid4()
        )
    )


@pytest.mark.integration
def test_out_of_scope_after_service_order_context():

    thread_id = create_thread()

    first = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Analise a OS 10235",
        },
        timeout=60,
    )

    assert first.status_code == 200


    second = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "como fazer bolo de cenoura?",
        },
        timeout=30,
    )

    assert second.status_code == 200

    data = second.json()

    assert (
        data["response_mode"]
        == "OUT_OF_SCOPE"
    )

    assert (
        data["sources"]
        == []
    )

    assert data["degraded"] is False


@pytest.mark.integration
def test_valid_queue_followup_still_uses_memory():

    thread_id = create_thread()

    first = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Analise a OS 10235",
        },
        timeout=60,
    )

    assert first.status_code == 200


    second = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "qual o status da fila?",
        },
        timeout=30,
    )

    assert second.status_code == 200

    data = second.json()

    assert (
        data["response_mode"]
        == "DIRECT"
    )

    assert (
        "erro"
        in data["answer"].lower()
    )

    assert (
        data["sources"]
        == []
    )
