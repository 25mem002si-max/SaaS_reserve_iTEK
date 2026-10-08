"""Client HTTP minimal pour les opérations métier du backend."""

from typing import Any, Dict, Optional

import httpx
import time

from app.config.settings import settings


class BackendClient:
    """Accès synchrone au backend de réservation."""

    def __init__(self) -> None:
        self.base_url = settings.backend_api_url.rstrip("/")
        self.timeout = settings.backend_timeout_seconds or 30
        self.headers: Dict[str, str] = {}
        if settings.backend_api_key:
            self.headers["Authorization"] = f"Bearer {settings.backend_api_key}"

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ) -> Dict[str, Any]:
        attempts = (settings.backend_retry_count or 0) + 1 if retryable else 1
        for attempt in range(attempts):
            try:
                response = httpx.request(
                    method,
                    f"{self.base_url}/{path.lstrip('/')}",
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                if response.status_code >= 500 and attempt < attempts - 1:
                    time.sleep(0.2 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("La réponse du backend doit être un objet JSON")
                return data
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt >= attempts - 1:
                    raise
                time.sleep(0.2 * (attempt + 1))
        raise RuntimeError("La requête backend a échoué")

    def check_availability(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/availability", payload, retryable=True)

    def lock_table(self, table_id: str, restaurant_id: str, duration_seconds: int) -> Dict[str, Any]:
        return self._request(
            "POST",
            f"/api/restaurants/{restaurant_id}/tables/{table_id}/lock",
            {"duration_seconds": duration_seconds},
        )

    def unlock_table(self, table_id: str, restaurant_id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            f"/api/restaurants/{restaurant_id}/tables/{table_id}/lock",
        )

    def create_reservation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/reservations", payload)

    def create_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/payments", payload)

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/payments/{payment_id}", retryable=True)
