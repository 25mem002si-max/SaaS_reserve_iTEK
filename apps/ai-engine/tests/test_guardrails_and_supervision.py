from app.guardrails.safety import PIIGuard, SafetyGuard
from app.services.supervision import AgentMonitor


def test_safety_rejects_invalid_payment_amount():
    assert not SafetyGuard.validate_payment_amount(0, "USD")
    assert not SafetyGuard.validate_payment_amount(1001, "USD")
    assert SafetyGuard.validate_payment_amount(10, "USD")


def test_pii_guard_masks_phone_numbers():
    masked = PIIGuard.mask_phone_number("+243123456789")

    assert masked != "+243123456789"
    assert "****" in masked


def test_monitor_counts_events_and_masks_phone(monkeypatch):
    events = []
    monitor = AgentMonitor()
    monkeypatch.setattr(monitor.logger, "info", lambda event, **kwargs: events.append((event, kwargs)))

    monitor.record(
        "payment_started",
        conversation_id="conversation-test",
        restaurant_id="restaurant-test",
        phone="+243123456789",
    )

    assert monitor.snapshot() == {"payment_started": 1}
    assert events[0][1]["phone"] != "+243123456789"
