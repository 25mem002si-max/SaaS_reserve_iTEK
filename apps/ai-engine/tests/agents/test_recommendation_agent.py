from app.agents.recommendation_agent import RecommendationAgent
from app.schemas.recommendation import RecommendationRequest


def test_recommendations_exclude_declared_allergy():
    agent = RecommendationAgent()
    result = agent.get_recommendations(
        RecommendationRequest(
            restaurant_id="restaurant-test",
            guests_count=2,
            allergies=["arachide"],
        )
    )

    assert result.items
    assert all("arachide" not in (item.name + (item.description or "")).lower() for item in result.items)


def test_budget_is_applied_to_recommendations():
    agent = RecommendationAgent()
    result = agent.get_recommendations(
        RecommendationRequest(
            restaurant_id="restaurant-test",
            guests_count=1,
            budget=5,
        )
    )

    assert result.items
    assert all(item.price <= 5 for item in result.items)
