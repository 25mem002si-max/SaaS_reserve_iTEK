from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_manager_can_get_own_restaurants():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/restaurants",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    restaurants = response.json()

    assert len(restaurants) >= 1

    restaurant_ids = [
        restaurant["id"]
        for restaurant in restaurants
    ]

    assert "c6074aec-4f3c-45d5-9f11-b98379ab43a1" in restaurant_ids


def test_manager_cannot_update_another_manager_restaurant():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    other_restaurant_id = "4165d61d-fcf4-4332-bce4-a46c649f51d9"

    response = client.put(
        f"/restaurants/{other_restaurant_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "description": "Tentative de modification",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Restaurant introuvable ou non attribué à ce manager."
    )


def test_manager_can_create_restaurant():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/restaurants",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Restaurant Test Pytest",
            "description": "Créé automatiquement par pytest",
            "address": "Kinshasa",
            "phone": "+243222222222",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Restaurant Test Pytest"
    assert data["description"] == "Créé automatiquement par pytest"
    assert data["address"] == "Kinshasa"
    assert data["phone"] == "+243222222222"


def test_client_cannot_create_restaurant():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/restaurants",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Restaurant Interdit",
            "description": "Un client ne devrait pas pouvoir créer ce restaurant",
            "address": "Kinshasa",
            "phone": "+243333333333",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Seuls les administrateurs et les managers peuvent créer un restaurant."
    )