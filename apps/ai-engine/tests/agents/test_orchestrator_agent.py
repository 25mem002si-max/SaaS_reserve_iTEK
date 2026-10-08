from app.agents.orchestrator import OrchestratorAgent
from app.graph import add_user_message, create_initial_state
from app.schemas.intent import IntentType


def test_routes_complete_reservation_to_reservation():
    agent = OrchestratorAgent()
    state = create_initial_state("conversation-test", "restaurant-test")
    add_user_message(state, "Je réserve demain à 20h pour 4 personnes")

    intent = agent.analyze(state)

    assert intent.type == IntentType.NEW_RESERVATION
    assert intent.confidence >= 0.75
    assert not intent.requires_clarification


def test_human_request_is_not_confused_with_group_size():
    agent = OrchestratorAgent()
    state = create_initial_state("conversation-test", "restaurant-test")
    add_user_message(state, "Je veux parler à un humain")

    intent = agent.analyze(state)

    assert intent.type == IntentType.HUMAN_HANDOFF
