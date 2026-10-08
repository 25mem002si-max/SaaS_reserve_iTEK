from app.agents.nlp_agent import NLPAgent
from app.agents.orchestrator import OrchestratorAgent
from app.config.settings import settings
from app.services.llm_service import LLMService


def test_llm_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "use_llm", False)

    assert NLPAgent()._use_llm is False
    assert OrchestratorAgent()._use_llm is False


def test_llm_service_loads_model_lazily(monkeypatch):
    service = LLMService()

    assert service._model is None


def test_nlp_respects_per_conversation_limit(monkeypatch):
    monkeypatch.setattr(settings, "use_llm", True)
    monkeypatch.setattr(settings, "llm_max_calls_per_conversation", 1)
    agent = NLPAgent()
    calls = []

    def fake_llm(_message, _context=""):
        calls.append(True)
        return agent._extract_with_patterns("une table")

    monkeypatch.setattr(agent, "_extract_with_llm", fake_llm)
    agent.extract("une table", conversation_id="limited-conversation")
    agent.extract("une autre table", conversation_id="limited-conversation")

    assert len(calls) == 1
