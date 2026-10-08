from app.agents.nlp_agent import NLPAgent
from app.config.settings import settings


def test_nlp_forwards_recent_conversation_context_to_llm(monkeypatch):
    monkeypatch.setattr(settings, "use_llm", True)
    monkeypatch.setattr(settings, "llm_max_calls_per_conversation", 1)
    agent = NLPAgent()
    captured = {}

    def fake_extract(message, context=""):
        captured["message"] = message
        captured["context"] = context
        return agent._extract_with_patterns(message)

    monkeypatch.setattr(agent, "_extract_with_llm", fake_extract)
    agent.extract(
        "demain",
        conversation_id="context-test",
        conversation_context="user: Je veux réserver\nassistant: Pour combien de personnes ?",
    )

    assert captured["message"] == "demain"
    assert "Pour combien de personnes" in captured["context"]
