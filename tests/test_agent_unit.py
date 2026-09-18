import asyncio

import pytest

import app.services.agent_service as agent_service


# ============================================================
# FUNCOES BASICAS
# ============================================================

def test_extract_service_order_id():

    assert (
        agent_service.extract_service_order_id(
            "Analise a OS 10235"
        )
        == 10235
    )


def test_extract_service_order_id_without_os():

    assert (
        agent_service.extract_service_order_id(
            "Qual é o contrato dela?"
        )
        is None
    )


def test_detect_contract_number_intent():

    assert (
        agent_service.detect_direct_intent(
            "Qual é o contrato dela?"
        )
        == "contract_number"
    )


def test_detect_vehicle_plate_intent():

    assert (
        agent_service.detect_direct_intent(
            "Qual é a placa dela?"
        )
        == "vehicle_plate"
    )


def test_analytical_question_is_not_direct():

    assert (
        agent_service.detect_direct_intent(
            "Por que ela está bloqueada?"
        )
        is None
    )


# ============================================================
# NORMALIZACAO DE LINGUAGEM
# ============================================================

def test_normalize_user_answer():

    text = (
        "A Ordem de Servico está BLOCKED, "
        "o contrato está INACTIVE e a fila está ERROR."
    )

    result = (
        agent_service.normalize_user_answer(
            text
        )
    )

    assert "BLOCKED" not in result
    assert "INACTIVE" not in result
    assert "ERROR" not in result

    assert "bloqueada" in result
    assert "inativo" in result
    assert "erro" in result
    assert "Ordem de Serviço" in result


# ============================================================
# FAST PATH
# ============================================================

def test_direct_contract_answer():

    state = {
        "trace_id": "pytest-direct-001",
        "service_order_id": 10235,
        "direct_intent": "contract_number",
        "diagnostic": """
        {
            "service_order": {
                "id": 10235,
                "status": "PENDING",
                "type": "INSTALLATION",
                "vehicle_plate": "DEF4G56"
            },
            "contract": {
                "id": 2002,
                "status": "INACTIVE"
            },
            "queue": {
                "status": "ERROR",
                "error": "Contract is inactive"
            },
            "diagnostic_status": "BLOCKED",
            "problems": []
        }
        """
    }

    result = asyncio.run(
        agent_service.direct_answer(
            state
        )
    )

    assert (
        result["response_mode"]
        == "DIRECT"
    )

    assert "2002" in result["answer"]


def test_direct_plate_answer():

    state = {
        "trace_id": "pytest-direct-002",
        "service_order_id": 10235,
        "direct_intent": "vehicle_plate",
        "diagnostic": """
        {
            "service_order": {
                "id": 10235,
                "status": "PENDING",
                "type": "INSTALLATION",
                "vehicle_plate": "DEF4G56"
            },
            "contract": {
                "id": 2002,
                "status": "INACTIVE"
            },
            "queue": {
                "status": "ERROR",
                "error": "Contract is inactive"
            },
            "diagnostic_status": "BLOCKED",
            "problems": []
        }
        """
    }

    result = asyncio.run(
        agent_service.direct_answer(
            state
        )
    )

    assert (
        result["response_mode"]
        == "DIRECT"
    )

    assert "DEF4G56" in result["answer"]


# ============================================================
# MODO DEGRADADO
# ============================================================

def test_degraded_answer_does_not_call_llm(
    monkeypatch,
):

    state = {
        "trace_id": "pytest-degraded-001",
        "service_order_id": 10235,
        "question": "Por que está bloqueada?",
        "degraded": True,
        "warnings": [
            "A base de conhecimento não estava disponível."
        ],
        "diagnostic": """
        {
            "service_order": {
                "id": 10235,
                "status": "PENDING",
                "type": "INSTALLATION",
                "vehicle_plate": "DEF4G56"
            },
            "contract": {
                "id": 2002,
                "status": "INACTIVE"
            },
            "queue": {
                "status": "ERROR",
                "error": "Contract is inactive"
            },
            "diagnostic_status": "BLOCKED",
            "problems": [
                "Contrato 2002 esta inativo.",
                "Fila de processamento esta com erro: Contract is inactive"
            ]
        }
        """
    }


    def fail_if_llm_is_called(*args, **kwargs):

        raise AssertionError(
            "O LLM não deveria ser chamado "
            "em modo degradado."
        )


    monkeypatch.setattr(
        agent_service,
        "chat",
        fail_if_llm_is_called,
    )


    result = asyncio.run(
        agent_service.generate_answer(
            state
        )
    )


    assert result["degraded"] is True

    assert (
        result["response_mode"]
        == "DEGRADED"
    )

    assert "bloqueada" in result["answer"]


# ============================================================
# FALHA DO RAG
# ============================================================

def test_forced_rag_failure(
    monkeypatch,
):

    monkeypatch.setattr(
        agent_service,
        "FORCE_RAG_ERROR",
        True,
    )


    state = {
        "trace_id": "pytest-rag-failure",
        "service_order_id": 10235,
        "diagnostic": "{}",
    }


    result = asyncio.run(
        agent_service.get_knowledge(
            state
        )
    )


    assert result["degraded"] is True

    assert result["knowledge"] == ""

    assert (
        result["knowledge_sources"]
        == []
    )

    assert len(
        result["warnings"]
    ) == 1


# ============================================================
# FALHA DO LLM
# ============================================================

def test_forced_llm_failure(
    monkeypatch,
):

    monkeypatch.setattr(
        agent_service,
        "FORCE_LLM_ERROR",
        True,
    )


    state = {
        "trace_id": "pytest-llm-failure",
        "service_order_id": 10235,
        "question": "Por que está bloqueada?",
        "degraded": False,
        "warnings": [],
        "knowledge": "Regra de teste.",
        "diagnostic": """
        {
            "service_order": {
                "id": 10235
            },
            "contract": {
                "id": 2002,
                "status": "INACTIVE"
            },
            "queue": {
                "status": "ERROR",
                "error": "Contract is inactive"
            },
            "diagnostic_status": "BLOCKED",
            "problems": [
                "Contrato 2002 esta inativo."
            ]
        }
        """
    }


    result = asyncio.run(
        agent_service.generate_answer(
            state
        )
    )


    assert result["degraded"] is True

    assert (
        result["response_mode"]
        == "DEGRADED"
    )

    assert len(
        result["warnings"]
    ) == 1


# ============================================================
# FALHA DO DIAGNOSTICO
# ============================================================

def test_forced_diagnostic_failure(
    monkeypatch,
):

    monkeypatch.setattr(
        agent_service,
        "FORCE_DIAGNOSTIC_ERROR",
        True,
    )


    state = {
        "trace_id": "pytest-diagnostic-failure",
        "service_order_id": 10235,
    }


    with pytest.raises(
        agent_service.AgentDependencyError
    ):

        asyncio.run(
            agent_service.get_diagnostic(
                state
            )
        )
