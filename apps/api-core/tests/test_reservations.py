from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app
from src.security.auth import create_access_token


client = TestClient(app)


RESTAURANT_ID = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"
TABLE_ID = "f96c9c8c-3cf9-49c2-ac76-fe230857d1d7"


# ============================================================
# HELPERS
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


def generate_unique_reservation_slot():
    """
    Génère une date et une heure très peu susceptibles
    d'exister déjà dans la base de données.
    """

    unique_number = uuid4().int

    days_offset = 1000 + (unique_number % 5000)

    reservation_date = (
        date.today() + timedelta(days=days_offset)
    ).isoformat()

    minutes_offset = (unique_number // 5000) % 240

    hour = 18 + (minutes_offset // 60)
    minute = minutes_offset % 60

    reservation_time = f"{hour:02d}:{minute:02d}:00"

    return reservation_date, reservation_time


def create_test_reservation(
    token,
    reservation_date=None,
    reservation_time=None,
    number_of_people=2,
):
    """
    Crée une réservation avec un créneau unique.

    Le test ne supprime aucune donnée existante.
    """

    if reservation_date is None or reservation_time is None:
        reservation_date, reservation_time = (
            generate_unique_reservation_slot()
        )

    response = client.post(
        "/reservations",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "table_id": TABLE_ID,
            "reservation_date": reservation_date,
            "reservation_time": reservation_time,
            "number_of_people": number_of_people,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


# ============================================================
# CLIENT - CREATE RESERVATION
# ============================================================

def test_client_can_create_reservation():
    token = login_client()

    reservation_date, reservation_time = (
        generate_unique_reservation_slot()
    )

    response = client.post(
        "/reservations",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "table_id": TABLE_ID,
            "reservation_date": reservation_date,
            "reservation_time": reservation_time,
            "number_of_people": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["table_id"] == TABLE_ID
    assert data["number_of_people"] == 2
    assert data["status"] == "pending"


# ============================================================
# MANAGER - CREATE RESERVATION FORBIDDEN
# ============================================================

def test_manager_cannot_create_reservation():
    token = login_manager()

    reservation_date, reservation_time = (
        generate_unique_reservation_slot()
    )

    response = client.post(
        "/reservations",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "table_id": TABLE_ID,
            "reservation_date": reservation_date,
            "reservation_time": reservation_time,
            "number_of_people": 2,
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Seuls les clients peuvent créer une réservation."
    )


# ============================================================
# CLIENT - GET OWN RESERVATIONS
# ============================================================

def test_client_can_get_own_reservations():
    token = login_client()

    create_test_reservation(token)

    response = client.get(
        "/reservations/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ============================================================
# CLIENT - GET ALL RESERVATIONS FORBIDDEN
# ============================================================

def test_client_cannot_get_all_reservations():
    token = login_client()

    response = client.get(
        "/reservations",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Accès réservé aux administrateurs et aux managers."
    )


# ============================================================
# MANAGER - GET RESERVATIONS
# ============================================================

def test_manager_can_get_reservations():
    token = login_manager()

    response = client.get(
        "/reservations",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ============================================================
# CLIENT - GET OWN RESERVATION
# ============================================================

def test_client_can_get_own_reservation():
    token = login_client()

    reservation = create_test_reservation(token)

    reservation_id = reservation["id"]

    response = client.get(
        f"/reservations/{reservation_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == reservation_id


# ============================================================
# MANAGER - GET RESERVATION FROM OWN RESTAURANT
# ============================================================

def test_manager_can_get_restaurant_reservation():
    client_token = login_client()
    manager_token = login_manager()

    reservation = create_test_reservation(client_token)

    reservation_id = reservation["id"]

    response = client.get(
        f"/reservations/{reservation_id}",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == reservation_id


# ============================================================
# CLIENT - UPDATE OWN RESERVATION
# ============================================================

def test_client_can_update_own_reservation():
    token = login_client()

    reservation = create_test_reservation(
        token,
        number_of_people=2,
    )

    reservation_id = reservation["id"]

    response = client.put(
        f"/reservations/{reservation_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "number_of_people": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == reservation_id
    assert data["number_of_people"] == 3


# ============================================================
# CLIENT - UPDATE ANOTHER CLIENT'S RESERVATION FORBIDDEN
# ============================================================

def test_client_cannot_update_another_reservation():
    client_token = login_client()

    reservation = create_test_reservation(
        client_token,
        number_of_people=2,
    )

    reservation_id = reservation["id"]

    other_client_id = "6bd4f00b-d9a6-4ffc-a8e6-f979c04ea5ce"

    other_token = create_access_token(other_client_id)

    response = client.put(
        f"/reservations/{reservation_id}",
        headers={
            "Authorization": f"Bearer {other_token}",
        },
        json={
            "number_of_people": 3,
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Vous n'êtes pas autorisé à modifier cette réservation."
    )


# ============================================================
# MANAGER - UPDATE RESERVATION
# ============================================================

def test_manager_can_update_reservation():
    client_token = login_client()
    manager_token = login_manager()

    reservation = create_test_reservation(
        client_token,
        number_of_people=2,
    )

    reservation_id = reservation["id"]

    response = client.put(
        f"/reservations/{reservation_id}",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "number_of_people": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == reservation_id
    assert data["number_of_people"] == 3


# ============================================================
# MANAGER - CONFIRM RESERVATION
# ============================================================

def test_manager_can_cancel_reservation():
    client_token = login_client()
    manager_token = login_manager()

    reservation = create_test_reservation(client_token)
    reservation_id = reservation["id"]

    response = client.patch(
        f"/reservations/{reservation_id}/status",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "status": "cancelled",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == reservation_id
    assert data["status"] == "cancelled"


# ============================================================
# CLIENT - CHANGE STATUS FORBIDDEN
# ============================================================

def test_client_cannot_change_status():
    client_token = login_client()

    reservation = create_test_reservation(client_token)

    reservation_id = reservation["id"]

    response = client.patch(
        f"/reservations/{reservation_id}/status",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
        json={
            "status": "confirmed",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Seuls les administrateurs et les managers "
        "peuvent modifier le statut."
    )


# ============================================================
# INVALID STATUS
# ============================================================

def test_invalid_reservation_status():
    client_token = login_client()
    manager_token = login_manager()

    reservation = create_test_reservation(client_token)

    reservation_id = reservation["id"]

    response = client.patch(
        f"/reservations/{reservation_id}/status",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "status": "invalid_status",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Statut invalide. Utilisez pending, confirmed ou cancelled."
    )


# ============================================================
# CLIENT - UNAVAILABLE TABLE CANNOT BE RESERVED
# ============================================================

def test_client_cannot_reserve_unavailable_table():
    client_token = login_client()
    manager_token = login_manager()

    table_response = client.post(
        f"/restaurants/{RESTAURANT_ID}/tables",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "table_number": 200,
            "capacity": 4,
            "status": "unavailable",
        },
    )

    assert table_response.status_code == 201, table_response.text

    table_id = table_response.json()["id"]

    reservation_date, reservation_time = (
        generate_unique_reservation_slot()
    )

    response = client.post(
        "/reservations",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "table_id": table_id,
            "reservation_date": reservation_date,
            "reservation_time": reservation_time,
            "number_of_people": 2,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Cette table n'est pas disponible pour une réservation."
    )