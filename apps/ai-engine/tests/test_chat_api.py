from fastapi.testclient import TestClient

from app.main import app
from app.graph import get_graph
from app.services.conversation_memory import ConversationMemoryService


client = TestClient(app)


def test_test_page_is_available():
    response = client.get("/test")

    assert response.status_code == 200
    assert "Console agents" in response.text
    assert "SpeechRecognition" in response.text
    assert "if (fromVoice) speak" in response.text


def test_chat_returns_greeting():
    response = client.post(
        "/api/chat",
        json={
            "conversation_id": "chat-api-test",
            "restaurant_id": "restaurant-test",
            "message": "Bonjour",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Bonjour ! Comment puis-je vous aider ?"
    assert response.json()["agent"] == "greeting"


def test_chat_keeps_reservation_details_across_messages():
    conversation_id = "chat-multi-turn-test-unique-2"
    payload = {
        "conversation_id": conversation_id,
        "restaurant_id": "restaurant-test",
        "customer_name": "Jean Dupont",
        "customer_phone": "+243123456789",
    }

    for message in ["5", "5 septembre à 20h"]:
        response = client.post("/api/chat", json={**payload, "message": message})
        assert response.status_code == 200

    result = response.json()
    assert result["next_action"] == "waiting_for_payment"
    assert "paiement" in result["message"].lower()


def test_chat_persists_assistant_messages_for_follow_up_context():
    conversation_id = "chat-assistant-context-test"
    payload = {
        "conversation_id": conversation_id,
        "restaurant_id": "restaurant-test",
    }

    first = client.post("/api/chat", json={**payload, "message": "Bonjour"})
    second = client.post("/api/chat", json={**payload, "message": "Je veux réserver"})

    assert first.status_code == 200
    assert second.status_code == 200
    checkpoint = get_graph().get_state({"configurable": {"thread_id": conversation_id}})
    messages = checkpoint.values["messages"]
    assert messages[0].role.value == "user"
    assert messages[1].role.value == "assistant"
    assert messages[1].content == first.json()["message"]
    assert messages[2].role.value == "user"
    assert messages[3].role.value == "assistant"


def test_conversation_memory_keeps_previous_messages_and_summary():
    class FakeRedis:
        def __init__(self):
            self.store = {}

        def get(self, key):
            value = self.store.get(key)
            return value.encode("utf-8") if isinstance(value, str) else value

        def set(self, key, value, ex=None):
            self.store[key] = value
            return True

    service = ConversationMemoryService(redis_client=FakeRedis())
    service.save_turn(
        "memory-summary-test",
        user_message="Bonjour",
        assistant_message="Bonjour ! Comment puis-je vous aider ?",
    )
    service.save_turn(
        "memory-summary-test",
        user_message="Je veux réserver demain pour 4 personnes",
        assistant_message="Très bien, quelle heure souhaitez-vous ?",
    )

    context = service.load_context("memory-summary-test")
    assert len(context["messages"]) >= 2
    assert "réserver" in context["summary"].lower()
    assert "demain" in context["summary"].lower()


def test_chat_restores_saved_conversation_state_after_graph_restart(monkeypatch):
    from types import SimpleNamespace

    from app.services import conversation_memory

    conversation_id = "chat-restore-after-restart"
    saved_state = {
        "conversation_id": conversation_id,
        "restaurant_id": "restaurant-test",
        "channel": "chat",
        "messages": [
            {"role": "user", "content": "Je veux réserver pour 4 personnes"},
            {"role": "assistant", "content": "Quel jour et à quelle heure ?"},
        ],
        "customer": {"name": "Jean Dupont", "phone": "+243123456789"},
        "extracted_info": {
            "date": None,
            "time": None,
            "guests_count": 4,
            "raw_text": "Je veux réserver pour 4 personnes",
            "confidence": 0.9,
        },
        "reservation": None,
        "payment": None,
        "iteration": 1,
        "metadata": {},
    }

    class FakeMemory:
        def __init__(self):
            self.saved_state = None

        def load_context(self, requested_conversation_id):
            assert requested_conversation_id == conversation_id
            return {"messages": saved_state["messages"], "state": saved_state, "summary": "4 personnes"}

        def restore_state(self, context):
            return ConversationMemoryService.restore_state(context)

        def save_turn(self, requested_conversation_id, **kwargs):
            self.saved_state = kwargs.get("state")

    class EmptyGraph:
        received_state = None

        def get_state(self, config):
            return SimpleNamespace(values={})

        def invoke(self, state, config):
            self.received_state = state
            return {**state, "current_agent": "ask_missing", "message": "À quelle heure ?"}

        def update_state(self, config, values):
            return None

    memory = FakeMemory()
    graph = EmptyGraph()
    monkeypatch.setattr(conversation_memory, "get_conversation_memory_service", lambda: memory)
    monkeypatch.setattr("app.main.get_graph", lambda: graph)

    response = client.post(
        "/api/chat",
        json={
            "conversation_id": conversation_id,
            "restaurant_id": "restaurant-test",
            "message": "demain soir à 20h",
        },
    )

    assert response.status_code == 200
    assert graph.received_state["extracted_info"].guests_count == 4
    assert graph.received_state["customer"].name == "Jean Dupont"
    assert [message.content for message in graph.received_state["messages"]] == [
        "Je veux réserver pour 4 personnes",
        "Quel jour et à quelle heure ?",
        "demain soir à 20h",
    ]
    assert memory.saved_state["extracted_info"].guests_count == 4


def test_conversation_memory_round_trips_typed_graph_state():
    from app.graph import add_user_message, create_initial_state
    from app.schemas.conversation import Message, MessageRole
    from app.schemas.customer import CustomerContext
    from app.schemas.nlp import ExtractedInformation

    class FakeRedis:
        def __init__(self):
            self.store = {}

        def get(self, key):
            value = self.store.get(key)
            return value.encode("utf-8") if isinstance(value, str) else value

        def set(self, key, value, ex=None):
            self.store[key] = value
            return True

    conversation_id = "memory-typed-state-round-trip"
    state = create_initial_state(
        conversation_id=conversation_id,
        restaurant_id="restaurant-test",
        customer=CustomerContext(name="Jean Dupont", phone="+243123456789"),
    )
    add_user_message(state, "Je veux réserver pour 4 personnes")
    state["messages"].append(Message(role=MessageRole.ASSISTANT, content="Quel jour souhaitez-vous ?"))
    state["extracted_info"] = ExtractedInformation(
        guests_count=4,
        raw_text="Je veux réserver pour 4 personnes",
        confidence=0.9,
    )

    service = ConversationMemoryService(redis_client=FakeRedis())
    service.save_turn(conversation_id, state=state)
    restored = service.restore_state(service.load_context(conversation_id))

    assert restored is not None
    assert restored["customer"].name == "Jean Dupont"
    assert restored["extracted_info"].guests_count == 4
    assert [message.role for message in restored["messages"]] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
    ]
    assert "4 personnes" in service.load_context(conversation_id)["summary"]


def test_chat_accepts_phone_after_reservation_details():
    conversation_id = "chat-phone-after-reservation-test"
    payload = {
        "conversation_id": conversation_id,
        "restaurant_id": "restaurant-test",
        "customer_name": "Jean Dupont",
    }

    first = client.post(
        "/api/chat",
        json={**payload, "message": "Je veux réserver demain à 20h pour 5 personnes"},
    )
    second = client.post("/api/chat", json={**payload, "message": "0972355597"})

    assert "téléphone" in first.json()["message"].lower()
    assert second.json()["next_action"] == "waiting_for_payment"


def test_chat_re_evaluates_each_new_intent_after_payment_request():
    conversation_id = "chat-intent-switch-after-payment"
    payload = {
        "conversation_id": conversation_id,
        "restaurant_id": "restaurant-test",
        "customer_name": "Jean Dupont",
        "customer_phone": "+243123456789",
    }

    reservation = client.post(
        "/api/chat",
        json={**payload, "message": "Je veux réserver pour 2 personnes ce soir"},
    )
    assert reservation.status_code == 200

    payment = client.post(
        "/api/chat",
        json={**payload, "message": "Je voudrais payer ma réservation"},
    )
    assert payment.json()["next_action"] == "waiting_for_payment"

    recommendation = client.post(
        "/api/chat",
        json={**payload, "message": "Donne-moi une recommandation de restaurant chic"},
    )
    assert recommendation.json()["agent"] == "recommendation_agent"
    assert "recommand" in recommendation.json()["message"].lower()

    phone = client.post(
        "/api/chat",
        json={**payload, "message": "Mon numéro est 0972355597"},
    )
    assert phone.json()["next_action"] == "waiting_for_payment"
    assert "déjà en cours" in phone.json()["message"].lower()

    cancellation = client.post(
        "/api/chat",
        json={**payload, "message": "Je veux annuler ma réservation"},
    )
    assert cancellation.json()["agent"] == "ask_missing"
    assert "référence" in cancellation.json()["message"].lower()


def test_chat_explains_how_to_pay_without_creating_duplicate_request():
    conversation_id = "chat-how-to-pay"
    payload = {
        "conversation_id": conversation_id,
        "restaurant_id": "restaurant-test",
        "customer_name": "Jean Dupont",
        "customer_phone": "+243123456789",
    }

    client.post(
        "/api/chat",
        json={**payload, "message": "Je veux réserver pour 6 personnes ce soir"},
    )
    client.post(
        "/api/chat",
        json={**payload, "message": "Comment dois-je payer ?"},
    )
    response = client.post(
        "/api/chat",
        json={**payload, "message": "Comment dois-je payer ?"},
    )

    assert response.json()["next_action"] == "waiting_for_payment"
    assert "M-Pesa" in response.json()["message"]
    assert "j'ai payé" in response.json()["message"]
