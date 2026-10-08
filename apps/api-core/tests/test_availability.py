from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


# ============================================================
# DONNÉES EXISTANTES UTILISÉES POUR LES TESTS
# ============================================================

ADMIN_EMAIL = "admin_test@example.com"
ADMIN_PASSWORD = "Admin123!"

CLIENT_EMAIL = "client_test@example.com"
CLIENT_PASSWORD = "Client123!"

MANAGER_EMAIL = "manager_test@example.com"
MANAGER_PASSWORD = "Manager123!"

RESTAURANT_ID = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

OTHER_RESTAURANT_ID = "4165d61d-fcf4-4332-bce4-a46c649f51d9"


# ============================================================
# HELPER
# ============================================================

def get_token(email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ============================================================
# CLIENT - CHECK AVAILABILITY
# ============================================================

def test_client_can_check_availability():
    token = get_token(
        CLIENT_EMAIL,
        CLIENT_PASSWORD,
    )

    response = client.get(
        f"/restaurants/{RESTAURANT_ID}/availability",
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "19:00:00",
            "number_of_people": 4,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["reservation_date"] == "2026-09-20"
    assert data["reservation_time"] == "19:00:00"
    assert data["number_of_people"] == 4
    assert "available_tables" in data


# ============================================================
# AVAILABILITY - TABLE CAPACITY
# ============================================================

def test_availability_respects_table_capacity():
    token = get_token(
        CLIENT_EMAIL,
        CLIENT_PASSWORD,
    )

    response = client.get(
        f"/restaurants/{RESTAURANT_ID}/availability",
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "19:00:00",
            "number_of_people": 6,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    for table in data["available_tables"]:
        assert table["capacity"] >= 6


# ============================================================
# AVAILABILITY - EXCLUDE RESERVED TABLE
# ============================================================

def test_availability_excludes_reserved_table():
    token = get_token(
        CLIENT_EMAIL,
        CLIENT_PASSWORD,
    )

    response = client.get(
        f"/restaurants/{RESTAURANT_ID}/availability",
        params={
            "reservation_date": "2026-09-06",
            "reservation_time": "19:00:00",
            "number_of_people": 4,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    table_numbers = [
        table["table_number"]
        for table in data["available_tables"]
    ]

    assert 2 not in table_numbers


# ============================================================
# AVAILABILITY - NO TABLE WITH ENOUGH CAPACITY
# ============================================================

def test_availability_returns_empty_when_no_table_can_fit():
    token = get_token(
        CLIENT_EMAIL,
        CLIENT_PASSWORD,
    )

    response = client.get(
        f"/restaurants/{RESTAURANT_ID}/availability",
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "19:00:00",
            "number_of_people": 100,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["available_tables"] == []


# ============================================================
# AVAILABILITY - RESTAURANT NOT FOUND
# ============================================================

def test_availability_restaurant_not_found():
    token = get_token(
        CLIENT_EMAIL,
        CLIENT_PASSWORD,
    )

    fake_restaurant_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(
        f"/restaurants/{fake_restaurant_id}/availability",
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "19:00:00",
            "number_of_people": 2,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


# ============================================================
# AVAILABILITY - INVALID NUMBER OF PEOPLE
# ============================================================

def test_availability_rejects_invalid_number_of_people():
    token = get_token(
        CLIENT_EMAIL,
        CLIENT_PASSWORD,
    )

    response = client.get(
        f"/restaurants/{RESTAURANT_ID}/availability",
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "19:00:00",
            "number_of_people": 0,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


# ============================================================
# MANAGER - CHECK OWN RESTAURANT
# ============================================================

def test_manager_can_check_own_restaurant():
    token = get_token(
        MANAGER_EMAIL,
        MANAGER_PASSWORD,
    )

    response = client.get(
        f"/restaurants/{RESTAURANT_ID}/availability",
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "19:00:00",
            "number_of_people": 2,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


# ============================================================
# MANAGER - OTHER RESTAURANT FORBIDDEN
# ============================================================

def test_manager_cannot_check_other_restaurant():
    token = get_token(
        MANAGER_EMAIL,
        MANAGER_PASSWORD,
    )

    response = client.get(
        f"/restaurants/{OTHER_RESTAURANT_ID}/availability",
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "19:00:00",
            "number_of_people": 2,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


# ============================================================
# AVAILABILITY - EXCLUDE UNAVAILABLE TABLE
# ============================================================

def test_availability_excludes_unavailable_table():
    client_token = get_token(
        CLIENT_EMAIL,
        CLIENT_PASSWORD,
    )

    manager_token = get_token(
        MANAGER_EMAIL,
        MANAGER_PASSWORD,
    )

    # Création d'une nouvelle table de test.
    table_response = client.post(
        f"/restaurants/{RESTAURANT_ID}/tables",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "table_number": 202,
            "capacity": 4,
            "status": "unavailable",
        },
    )

    assert table_response.status_code == 201, table_response.text

    table_id = table_response.json()["id"]

    # Vérifier les disponibilités.
    response = client.get(
        f"/restaurants/{RESTAURANT_ID}/availability",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
        params={
            "reservation_date": "2026-09-20",
            "reservation_time": "21:00:00",
            "number_of_people": 2,
        },
    )

    assert response.status_code == 200

    available_table_ids = [
        table["id"]
        for table in response.json()["available_tables"]
    ]

    # La table unavailable ne doit pas apparaître.
    assert table_id not in available_table_ids