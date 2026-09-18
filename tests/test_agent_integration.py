import uuid

import httpx
import pytest


BASE_URL = (
    "http://127.0.0.1:8000"
)


def create_thread():

    return (
        "pytest-"
        +
        str(
            uuid.uuid4()
        )
    )


@pytest.mark.integration
def test_health():

    response = httpx.get(
        f"{BASE_URL}/health",
        timeout=10,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


@pytest.mark.integration
def test_blocked_service_order_uses_ai_and_rag():

    thread_id = create_thread()


    response = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Por que a OS 10235 está bloqueada?"
        },
        timeout=60,
    )


    assert response.status_code == 200


    data = response.json()


    assert (
        data["service_order_id"]
        == 10235
    )


    assert (
        data["status"]
        == "BLOCKED"
    )


    assert (
        data["response_mode"]
        == "AI"
    )


    assert (
        data["degraded"]
        is False
    )


    assert data["answer"]


    assert (
        "inativo"
        in data["answer"].lower()
    )


    assert (
        isinstance(
            data["sources"],
            list,
        )
    )


    assert (
        len(
            data["sources"]
        )
        > 0
    )


@pytest.mark.integration
def test_same_thread_uses_memory_and_fast_path():

    thread_id = create_thread()


    first = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Analise a OS 10235"
        },
        timeout=60,
    )


    assert (
        first.status_code
        == 200
    )


    second = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Qual é o contrato dela?"
        },
        timeout=30,
    )


    assert (
        second.status_code
        == 200
    )


    data = second.json()


    assert (
        data["service_order_id"]
        == 10235
    )


    assert (
        data["response_mode"]
        == "DIRECT"
    )


    assert (
        "2002"
        in data["answer"]
    )


    # Fast path nao deve consultar RAG.
    assert (
        data["sources"]
        == []
    )


@pytest.mark.integration
def test_fast_path_plate():

    thread_id = create_thread()


    first = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Analise a OS 10235"
        },
        timeout=60,
    )


    assert (
        first.status_code
        == 200
    )


    response = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Qual é a placa dela?"
        },
        timeout=30,
    )


    assert (
        response.status_code
        == 200
    )


    data = response.json()


    assert (
        data["response_mode"]
        == "DIRECT"
    )


    assert (
        "DEF4G56"
        in data["answer"]
    )


@pytest.mark.integration
def test_service_order_10236_is_ok():

    thread_id = create_thread()


    response = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                thread_id,

            "message":
                "Analise a OS 10236"
        },
        timeout=60,
    )


    assert (
        response.status_code
        == 200
    )


    data = response.json()


    assert (
        data["service_order_id"]
        == 10236
    )


    assert (
        data["status"]
        == "OK"
    )


    # Como nao esta BLOCKED, nao precisa de RAG.
    assert (
        data["sources"]
        == []
    )


@pytest.mark.integration
def test_unknown_thread_without_os_returns_400():

    response = httpx.post(
        f"{BASE_URL}/agent/chat",
        json={
            "thread_id":
                create_thread(),

            "message":
                "Qual é o contrato dela?"
        },
        timeout=30,
    )


    assert (
        response.status_code
        == 400
    )
