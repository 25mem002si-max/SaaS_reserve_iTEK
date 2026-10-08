"""Supervision légère et sans PII pour les agents."""

from collections import Counter
from threading import Lock
from typing import Any, Dict

from app.config.logging import get_logger
from app.guardrails.safety import get_pii_guard


class AgentMonitor:
    """Enregistre les événements métier utiles au suivi opérationnel."""

    def __init__(self) -> None:
        self.logger = get_logger()
        self._counts: Counter[str] = Counter()
        self._lock = Lock()

    def record(
        self,
        event: str,
        conversation_id: str | None = None,
        restaurant_id: str | None = None,
        **details: Any,
    ) -> None:
        """Publie un événement structuré sans journaliser les données sensibles."""
        safe_details = dict(details)
        if "phone" in safe_details:
            safe_details["phone"] = get_pii_guard().mask_phone_number(str(safe_details["phone"]))
        with self._lock:
            self._counts[event] += 1
        self.logger.info(
            event,
            conversation_id=conversation_id,
            restaurant_id=restaurant_id,
            **safe_details,
        )

    def snapshot(self) -> Dict[str, int]:
        """Retourne un instantané des compteurs par événement."""
        with self._lock:
            return dict(self._counts)


_monitor = AgentMonitor()


def get_agent_monitor() -> AgentMonitor:
    """Retourne le moniteur partagé des agents."""
    return _monitor
