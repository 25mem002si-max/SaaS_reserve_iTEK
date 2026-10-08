from datetime import datetime

from app.agents.payment_agent import PaymentAgent
from app.config.settings import settings
from app.schemas.customer import CustomerContext
from app.schemas.payment import PaymentResult, PaymentStatus, PaymentProvider
from app.schemas.reservation import ReservationData


def make_state(phone: str | None = "+243123456789") -> dict:
    return {
        "conversation_id": "conversation-payment-test",
        "restaurant_id": "restaurant-test",
        "customer": CustomerContext(name="Jean Dupont", phone=phone),
        "reservation": ReservationData(
            date=datetime(2026, 9, 4, 20, 0),
            time="20:00",
            guests_count=4,
            deposit_required=True,
            deposit_amount=10.0,
            currency="USD",
            customer_name="Jean Dupont",
            customer_phone=phone,
        ),
        "reservation_confirmation": {"reservation_id": "reservation-test"},
    }


def test_local_payment_is_pending(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", False)
    agent = PaymentAgent()

    result = agent.process_payment(make_state())

    assert result["next_action"] == "waiting_for_payment"
    assert result["payment"].status == PaymentStatus.PENDING
    assert result["payment"].reservation_id == "reservation-test"
    assert result["payment"].amount == 10.0


def test_payment_requires_phone_number(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", False)
    agent = PaymentAgent()

    result = agent.process_payment(make_state(phone=None))

    assert result["next_action"] == "ask_phone"
    assert "téléphone" in result["message"]


def test_backend_payment_response_is_validated(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", True)
    agent = PaymentAgent()
    response = PaymentResult(
        payment_id="payment-test",
        reservation_id="reservation-test",
        status=PaymentStatus.SUCCESS,
        amount=10.0,
        currency="USD",
        provider=PaymentProvider.M_PESA,
        transaction_id="transaction-test",
        paid_at=datetime(2026, 9, 3, 12, 0),
    )
    calls = []
    monkeypatch.setattr(
        agent.backend,
        "create_payment",
        lambda payload: calls.append(payload) or response.model_dump(mode="json"),
    )

    result = agent.create_payment_request(
        reservation_id="reservation-test",
        restaurant_id="restaurant-test",
        amount=10.0,
        currency="USD",
        phone_number="+243123456789",
        provider="m_pesa",
    )

    assert result == response
    assert calls[0]["reservation_id"] == "reservation-test"
    assert calls[0]["phone_number"] == "+243123456789"


def test_backend_payment_status_is_validated(monkeypatch):
    monkeypatch.setattr(settings, "backend_enabled", True)
    agent = PaymentAgent()
    response = PaymentResult(
        payment_id="payment-test",
        reservation_id="reservation-test",
        status=PaymentStatus.PENDING,
        amount=10.0,
        currency="USD",
        provider=PaymentProvider.M_PESA,
    )
    monkeypatch.setattr(
        agent.backend,
        "get_payment_status",
        lambda payment_id: response.model_dump(mode="json"),
    )

    result = agent.get_payment_status("payment-test")

    assert result == response
