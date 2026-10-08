from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


RESTAURANT_ID = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

TABLE_ID = "b8a80523-4a11-4881-92aa-0d372c5939f7"


# ============================================================
# AUTHENTIFICATION
# ============================================================

def login_client():
    response = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def login_manager():
    response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def login_admin():
    response = client.post(
        "/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "Admin123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ============================================================
# CRÉER UNE RÉSERVATION DE TEST
# ============================================================

def create_test_reservation(client_token):
    """
    Crée une réservation à une date future libre.
    Si la date est déjà utilisée, on essaie le jour suivant.
    """

    reservation_date = date.today() + timedelta(days=100)

    while True:
        date_string = reservation_date.isoformat()

        response = client.post(
            "/reservations",
            headers={
                "Authorization": f"Bearer {client_token}",
            },
            json={
                "restaurant_id": RESTAURANT_ID,
                "table_id": TABLE_ID,
                "reservation_date": date_string,
                "reservation_time": "20:00:00",
                "number_of_people": 2,
            },
        )

        if response.status_code == 201:
            return response.json()["id"]

        if response.status_code == 409:
            reservation_date += timedelta(days=1)
            continue

        assert response.status_code == 201, response.json()


# ============================================================
# CRÉER UN PAIEMENT DE TEST
# ============================================================

def create_test_payment(
    client_token,
    reservation_id,
    amount="50.00",
):
    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
        json={
            "reservation_id": reservation_id,
            "amount": amount,
            "currency": "USD",
            "payment_method": "card",
        },
    )

    assert response.status_code == 201, response.json()

    return response.json()


# ============================================================
# CRÉER UN PAIEMENT
# ============================================================

def test_client_can_create_payment():
    token = login_client()

    reservation_id = create_test_reservation(token)

    payment = create_test_payment(
        token,
        reservation_id,
    )

    assert payment["reservation_id"] == reservation_id
    assert payment["amount"] == "50.00"
    assert payment["currency"] == "USD"
    assert payment["status"] == "pending"
    assert payment["payment_method"] == "card"
    assert payment["transaction_id"] is None


# ============================================================
# VOIR MES PAIEMENTS
# ============================================================

def test_client_can_get_own_payments():
    token = login_client()

    reservation_id = create_test_reservation(token)

    payment = create_test_payment(
        token,
        reservation_id,
    )

    response = client.get(
        "/payments/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    payments = response.json()

    assert any(
        item["id"] == payment["id"]
        for item in payments
    )


# ============================================================
# VOIR LE PAIEMENT D'UNE RÉSERVATION
# ============================================================

def test_client_can_get_payment_by_reservation():
    token = login_client()

    reservation_id = create_test_reservation(token)

    payment = create_test_payment(
        token,
        reservation_id,
    )

    response = client.get(
        f"/payments/reservation/{reservation_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment["id"]
    assert data["reservation_id"] == reservation_id
    assert data["amount"] == "50.00"
    assert data["currency"] == "USD"
    assert data["status"] == "pending"


# ============================================================
# MANAGER → MARQUER LE PAIEMENT COMME PAYÉ
# ============================================================

def test_manager_can_mark_payment_as_paid():
    client_token = login_client()
    manager_token = login_manager()

    reservation_id = create_test_reservation(client_token)

    payment = create_test_payment(
        client_token,
        reservation_id,
    )

    payment_id = payment["id"]

    transaction_id = f"TEST-TXN-{uuid4()}"

    response = client.patch(
        f"/payments/{payment_id}/status",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "status": "paid",
            "transaction_id": transaction_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["status"] == "paid"
    assert data["transaction_id"] == transaction_id


# ============================================================
# CLIENT → NE PEUT PAS MODIFIER LE STATUT
# ============================================================

def test_client_cannot_update_payment_status():
    client_token = login_client()

    reservation_id = create_test_reservation(client_token)

    payment = create_test_payment(
        client_token,
        reservation_id,
    )

    response = client.patch(
        f"/payments/{payment['id']}/status",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
        json={
            "status": "failed",
            "transaction_id": f"CLIENT-FORBIDDEN-{uuid4()}",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Accès réservé aux administrateurs et aux managers."
    )


# ============================================================
# ADMIN → MODIFIER LE STATUT
# ============================================================

def test_admin_can_update_payment_status():
    client_token = login_client()
    admin_token = login_admin()

    reservation_id = create_test_reservation(client_token)

    payment = create_test_payment(
        client_token,
        reservation_id,
    )

    payment_id = payment["id"]

    transaction_id = f"ADMIN-TXN-{uuid4()}"

    response = client.patch(
        f"/payments/{payment_id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "status": "failed",
            "transaction_id": transaction_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["status"] == "failed"
    assert data["transaction_id"] == transaction_id


# ============================================================
# EMPÊCHER LES PAIEMENTS DUPLIQUÉS
# ============================================================

def test_client_cannot_create_duplicate_payment():
    token = login_client()

    reservation_id = create_test_reservation(token)

    create_test_payment(
        token,
        reservation_id,
    )

    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "reservation_id": reservation_id,
            "amount": "50.00",
            "currency": "USD",
            "payment_method": "card",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Un paiement existe déjà pour cette réservation."
    )


# ============================================================
# EMPÊCHER LE PAIEMENT D'UNE RÉSERVATION ANNULÉE
# ============================================================

def test_client_cannot_pay_cancelled_reservation():
    client_token = login_client()

    reservation_id = create_test_reservation(client_token)

    manager_token = login_manager()

    cancel_response = client.patch(
        f"/reservations/{reservation_id}/status",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "status": "cancelled",
        },
    )

    assert cancel_response.status_code == 200

    assert cancel_response.json()["status"] == "cancelled"

    payment_response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
        json={
            "reservation_id": reservation_id,
            "amount": "50.00",
            "currency": "USD",
            "payment_method": "card",
        },
    )

    assert payment_response.status_code == 400

    assert payment_response.json()["detail"] == (
        "Une réservation annulée ne peut pas être payée."
    )


# ============================================================
# EMPÊCHER LE RETOUR DE PAID VERS PENDING
# ============================================================

def test_admin_cannot_revert_paid_payment_to_pending():
    client_token = login_client()

    reservation_id = create_test_reservation(client_token)

    payment = create_test_payment(
        client_token,
        reservation_id,
    )

    payment_id = payment["id"]

    admin_token = login_admin()

    transaction_id = f"TXN-PAID-{uuid4()}"

    paid_response = client.patch(
        f"/payments/{payment_id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "status": "paid",
            "transaction_id": transaction_id,
        },
    )

    assert paid_response.status_code == 200, paid_response.text
    assert paid_response.json()["status"] == "paid"

    revert_response = client.patch(
        f"/payments/{payment_id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "status": "pending",
        },
    )

    assert revert_response.status_code == 400, revert_response.text

    assert (
        revert_response.json()["detail"]
        == "Le statut de ce paiement ne peut plus être modifié."
    )


# ============================================================
# EMPÊCHER L'ANNULATION D'UN PAIEMENT DÉJÀ PAYÉ
# ============================================================

def test_admin_cannot_cancel_paid_payment():
    client_token = login_client()

    reservation_id = create_test_reservation(client_token)

    payment = create_test_payment(
        client_token,
        reservation_id,
        amount="75.00",
    )

    payment_id = payment["id"]

    admin_token = login_admin()

    transaction_id = f"TXN-PAID-{uuid4()}"

    paid_response = client.patch(
        f"/payments/{payment_id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "status": "paid",
            "transaction_id": transaction_id,
        },
    )

    assert paid_response.status_code == 200, paid_response.text
    assert paid_response.json()["status"] == "paid"

    cancel_response = client.patch(
        f"/payments/{payment_id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "status": "cancelled",
        },
    )

    assert cancel_response.status_code == 400, cancel_response.text

    assert (
        cancel_response.json()["detail"]
        == "Le statut de ce paiement ne peut plus être modifié."
    )