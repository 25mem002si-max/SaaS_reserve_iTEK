from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_manager_can_get_own_restaurant_tables():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    restaurant_id = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

    response = client.get(
        f"/restaurants/{restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_manager_cannot_get_another_restaurant_tables():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    other_restaurant_id = "4165d61d-fcf4-4332-bce4-a46c649f51d9"

    response = client.get(
        f"/restaurants/{other_restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


def test_manager_can_create_table():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    restaurant_id = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

    response = client.post(
        f"/restaurants/{restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "table_number": 30,
            "capacity": 4,
            "status": "available",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == restaurant_id
    assert data["table_number"] == 30
    assert data["capacity"] == 4
    assert data["status"] == "available"


def test_manager_cannot_create_table_in_another_restaurant():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    other_restaurant_id = "4165d61d-fcf4-4332-bce4-a46c649f51d9"

    response = client.post(
        f"/restaurants/{other_restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "table_number": 40,
            "capacity": 4,
            "status": "available",
        },
    )

    assert response.status_code == 404


def test_manager_can_update_own_restaurant_table():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    table_id = "76ce5ff9-d5ee-4102-97c8-6f13347dd679"

    response = client.put(
        f"/restaurants/tables/{table_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "capacity": 6,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == table_id
    assert data["capacity"] == 6
def test_client_cannot_update_table():
    login = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    table_id = "76ce5ff9-d5ee-4102-97c8-6f13347dd679"

    response = client.put(
        f"/restaurants/tables/{table_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "capacity": 8,
        },
    )

    assert response.status_code == 403
def test_manager_can_get_own_restaurant_table():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    table_id = "76ce5ff9-d5ee-4102-97c8-6f13347dd679"

    response = client.get(
        f"/restaurants/tables/{table_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == table_id
    assert data["restaurant_id"] == (
        "c6074aec-4f3c-45d5-9f11-b98379ab43a1"
    )
def test_client_can_get_restaurant_table():
    login = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    table_id = "76ce5ff9-d5ee-4102-97c8-6f13347dd679"

    response = client.get(
        f"/restaurants/tables/{table_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == table_id
    assert data["restaurant_id"] == (
        "c6074aec-4f3c-45d5-9f11-b98379ab43a1"
    )
def test_manager_can_get_updated_restaurant_table():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    table_id = "76ce5ff9-d5ee-4102-97c8-6f13347dd679"

    response = client.get(
        f"/restaurants/tables/{table_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == table_id
    assert data["capacity"] == 6
def test_manager_can_delete_restaurant_table():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    restaurant_id = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

    create_response = client.post(
        f"/restaurants/{restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "table_number": 99,
            "capacity": 2,
            "status": "available",
        },
    )

    assert create_response.status_code == 201

    table_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/restaurants/tables/{table_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert delete_response.status_code == 204
def test_manager_can_create_table_with_maintenance_status():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    restaurant_id = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

    response = client.post(
        f"/restaurants/{restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "table_number": 101,
            "capacity": 4,
            "status": "maintenance",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "maintenance"


def test_manager_can_create_table_with_unavailable_status():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    restaurant_id = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

    response = client.post(
        f"/restaurants/{restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "table_number": 102,
            "capacity": 4,
            "status": "unavailable",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "unavailable"


def test_manager_cannot_create_table_with_invalid_status():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    restaurant_id = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"

    response = client.post(
        f"/restaurants/{restaurant_id}/tables",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "table_number": 103,
            "capacity": 4,
            "status": "bonjour",
        },
    )

    assert response.status_code == 422


def test_manager_cannot_update_table_with_invalid_status():
    login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    table_id = "76ce5ff9-d5ee-4102-97c8-6f13347dd679"

    response = client.put(
        f"/restaurants/tables/{table_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "status": "bonjour",
        },
    )

    assert response.status_code == 422