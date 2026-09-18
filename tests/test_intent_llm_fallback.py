import types

import app.intents.llm_classifier as classifier
import app.services.agent_service as agent_service


def _response(content: str):
    return types.SimpleNamespace(
        message=types.SimpleNamespace(
            content=content,
        )
    )


def test_llm_classifier_maps_natural_queue_question(monkeypatch):
    monkeypatch.setattr(
        classifier,
        "chat",
        lambda **kwargs: _response(
            '{"intent":"queue_status","confidence":0.96}'
        ),
    )

    result = classifier.classify_intent_with_llm(
        "me fala o que aconteceu com a fila"
    )

    assert result.intent == "queue_status"
    assert result.out_of_scope is False
    assert result.confidence == 0.96


def test_llm_classifier_rejects_low_confidence(monkeypatch):
    monkeypatch.setattr(
        classifier,
        "chat",
        lambda **kwargs: _response(
            '{"intent":"vehicle_plate","confidence":0.42}'
        ),
    )

    result = classifier.classify_intent_with_llm(
        "me passa aquele dado do carro"
    )

    assert result.intent is None
    assert result.out_of_scope is False


def test_llm_classifier_can_mark_out_of_scope(monkeypatch):
    monkeypatch.setattr(
        classifier,
        "chat",
        lambda **kwargs: _response(
            '{"intent":"out_of_scope","confidence":0.99}'
        ),
    )

    result = classifier.classify_intent_with_llm(
        "qual a receita de bolo?"
    )

    assert result.intent is None
    assert result.out_of_scope is True


def test_scope_guard_allows_contextual_status_followup():
    assert agent_service.is_fleetops_scope(
        "qual a situação dela agora?",
        has_service_order_context=True,
    ) is True


def test_scope_guard_does_not_expand_without_context():
    assert agent_service.is_fleetops_scope(
        "qual a situação dela agora?",
        has_service_order_context=False,
    ) is False
