from datetime import datetime
from types import SimpleNamespace

from app.agents.reservation_agent import ReservationAgent
from app.schemas.availability import AvailabilityResult, TableOption, TableStatus
from app.schemas.customer import CustomerContext
from app.schemas.reservation import ReservationData


def make_reservation() -> ReservationData:
    return ReservationData(
        date=datetime(2026, 9, 4, 9, 0),
        time="20:00",
        guests_count=2,
        customer_name="Jean Dupont",
        customer_phone="+243123456789",
    )


def make_state(reservation: ReservationData) -> dict:
    return {
        "conversation_id": "conversation-test",
        "restaurant_id": "restaurant-test",
        "reservation": reservation,
        "customer": CustomerContext(name="Jean Dupont", phone="+243123456789"),
    }


def test_process_reservation_uses_requested_time(monkeypatch):
    monkeypatch.setattr("app.agents.reservation_agent.settings.backend_enabled", False)
    agent = ReservationAgent()
    reservation = make_reservation()

    result = agent.process_reservation(make_state(reservation))

    assert result["next_action"] == "confirmation"
    assert reservation.date == datetime(2026, 9, 4, 20, 0)
    assert result["reservation_confirmation"].date == datetime(2026, 9, 4, 20, 0)


def test_process_reservation_releases_table_when_creation_fails(monkeypatch):
    monkeypatch.setattr("app.agents.reservation_agent.settings.backend_enabled", False)
    agent = ReservationAgent()
    reservation = make_reservation()
    released = []

    monkeypatch.setattr(agent, "create_reservation", lambda *_args: None)
    monkeypatch.setattr(
        agent,
        "unlock_table",
        lambda table_id, restaurant_id: released.append((table_id, restaurant_id)) or True,
    )

    result = agent.process_reservation(make_state(reservation))

    assert result["next_action"] == "error"
    assert result["error"] == "Échec de la création de la réservation"
    assert released == [("table-003", "restaurant-test")]


def test_process_reservation_releases_table_on_backend_exception(monkeypatch):
    monkeypatch.setattr("app.agents.reservation_agent.settings.backend_enabled", False)
    agent = ReservationAgent()
    reservation = make_reservation()
    released = []

    def fail_creation(*_args):
        raise RuntimeError("backend indisponible")

    monkeypatch.setattr(agent, "create_reservation", fail_creation)
    monkeypatch.setattr(
        agent,
        "unlock_table",
        lambda table_id, restaurant_id: released.append((table_id, restaurant_id)) or True,
    )

    result = agent.process_reservation(make_state(reservation))

    assert result["next_action"] == "retry"
    assert released == [("table-003", "restaurant-test")]


def test_backend_availability_response_is_validated(monkeypatch):
    monkeypatch.setattr("app.agents.reservation_agent.settings.backend_enabled", True)
    agent = ReservationAgent()
    response = AvailabilityResult(
        restaurant_id="restaurant-test",
        date=datetime(2026, 9, 4, 20, 0),
        guests_count=2,
        available=True,
        tables=[
            TableOption(
                table_id="table-9",
                table_label="Table 9",
                capacity=2,
                zone="Intérieur",
                status=TableStatus.AVAILABLE,
            )
        ],
    )
    calls = []
    monkeypatch.setattr(
        agent.backend,
        "check_availability",
        lambda payload: calls.append(payload) or response.model_dump(mode="json"),
    )

    result = agent.check_availability("restaurant-test", datetime(2026, 9, 4, 20, 0), 2)

    assert result == response
    assert calls[0]["restaurant_id"] == "restaurant-test"
    assert calls[0]["guests_count"] == 2
