from datetime import datetime

from app.agents.notification_agent import NotificationAgent
from app.schemas.reservation import ReservationConfirmation, ReservationStatus


def test_confirmation_message_contains_booking_details():
    agent = NotificationAgent()
    confirmation = ReservationConfirmation(
        reservation_id="reservation-test",
        table_id="table-1",
        table_label="Table 1",
        customer_name="Jean Dupont",
        date=datetime(2026, 9, 4, 20, 0),
        guests_count=4,
        status=ReservationStatus.PENDING_PAYMENT,
        deposit_amount=10,
        currency="USD",
        message="En attente",
    )

    message = agent.format_confirmation_message(confirmation)

    assert "04/09/2026" in message
    assert "20:00" in message
    assert "reservation-test" in message
    assert "en attente de paiement" in message


def test_missing_confirmation_is_reported():
    result = NotificationAgent().process_notification({"conversation_id": "conversation-test"})

    assert result["next_action"] == "error"
