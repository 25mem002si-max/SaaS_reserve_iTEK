from datetime import date, datetime

from app.agents.nlp_agent import NLPAgent


def test_extracts_weekday_evening_and_couple(monkeypatch):
    agent = NLPAgent()
    monkeypatch.setattr(
        agent,
        "_extract_with_llm",
        lambda _message, _context="": agent._extract_with_patterns(_message),
    )

    result = agent.extract("Je réserve vendredi dans la soirée pour un couple")

    assert result.date is not None
    assert result.date.date() > date.today()
    assert result.time == "19:00"
    assert result.guests_count == 2


def test_date_question_is_not_special_occasion():
    agent = NLPAgent()

    result = agent._extract_with_patterns("Quelle date est disponible pour une table ?")

    assert result.special_occasion is None


def test_extract_result_reports_missing_fields():
    agent = NLPAgent()

    result = agent.get_nlp_result(agent._extract_with_patterns("Une table pour 3 personnes"))

    assert not result.is_complete
    assert {item.field for item in result.missing} == {"date", "time"}
