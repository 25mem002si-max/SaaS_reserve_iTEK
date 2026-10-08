from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_user_can_get_own_profile():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert me_response.status_code == 200

    user_id = me_response.json()["id"]

    response = client.get(
        f"/users/{user_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == user_id
    assert response.json()["email"] == "manager_test@example.com"


def test_user_cannot_get_another_user_profile():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # ID d'un autre utilisateur existant
    other_user_id = "53576ac2-9b5c-4096-8768-e7a3c585f96d"

    response = client.get(
        f"/users/{other_user_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_user_can_update_own_profile():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert me_response.status_code == 200

    user_id = me_response.json()["id"]

    response = client.put(
        f"/users/{user_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "username": "manager_test_auto",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "manager_test_auto"


def test_user_cannot_change_own_role():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert me_response.status_code == 200

    user_id = me_response.json()["id"]

    response = client.put(
        f"/users/{user_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "role": "admin",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Seul un administrateur peut modifier un rôle."