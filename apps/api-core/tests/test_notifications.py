from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_client_can_get_own_notifications():
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
        "/notifications/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_can_create_notification():
    login_response = client.post(
        "/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "Admin123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": "b64bc08d-05b1-4cb9-a3ef-96f2682782a3",
            "title": "Test notification",
            "message": "Votre réservation a été créée.",
            "type": "reservation_created",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == "b64bc08d-05b1-4cb9-a3ef-96f2682782a3"
    assert data["title"] == "Test notification"
    assert data["message"] == "Votre réservation a été créée."
    assert data["type"] == "reservation_created"
    assert data["is_read"] is False


def test_client_can_mark_notification_as_read():
    # Connexion Admin pour créer une notification
    admin_login = client.post(
        "/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "Admin123!",
        },
    )

    assert admin_login.status_code == 200

    admin_token = admin_login.json()["access_token"]

    create_response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "user_id": "b64bc08d-05b1-4cb9-a3ef-96f2682782a3",
            "title": "Notification à lire",
            "message": "Cette notification doit être marquée comme lue.",
            "type": "reservation_confirmed",
        },
    )

    assert create_response.status_code == 201

    notification_id = create_response.json()["id"]

    # Connexion du Client
    client_login = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )

    assert client_login.status_code == 200

    client_token = client_login.json()["access_token"]

    # Marquer la notification comme lue
    response = client.patch(
        f"/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == notification_id
    assert data["is_read"] is True
def test_client_cannot_access_another_user_notification():
    # Connexion Admin
    admin_login = client.post(
        "/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "Admin123!",
        },
    )

    assert admin_login.status_code == 200

    admin_token = admin_login.json()["access_token"]

    # Création d'une notification destinée à manager_test
    create_response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "user_id": "c6e46664-0a34-4766-9942-a5183e058e4f",
            "title": "Notification privée",
            "message": "Cette notification appartient au manager.",
            "type": "private_test",
        },
    )

    assert create_response.status_code == 201

    notification_id = create_response.json()["id"]

    # Connexion du client_test
    client_login = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )

    assert client_login.status_code == 200

    client_token = client_login.json()["access_token"]

    # Le client tente d'accéder à la notification du manager
    response = client.get(
        f"/notifications/{notification_id}",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Accès interdit à cette notification."
def test_client_cannot_create_notification():
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
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": "b64bc08d-05b1-4cb9-a3ef-96f2682782a3",
            "title": "Notification interdite",
            "message": "Le client ne doit pas pouvoir créer ceci.",
            "type": "permission_test",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Accès réservé aux administrateurs."
from datetime import date, timedelta

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)

RESTAURANT_ID = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"
TABLE_ID = "3c463f5d-a759-42c9-9a2e-ec332f7099f7"


def create_test_reservation(client_token):
    """
    Crée une réservation à une date future libre.
    Si la date est déjà utilisée, on essaie le jour suivant.
    """

    reservation_date = date.today() + timedelta(days=100)

    while True:
        date_string = reservation_date.isoformat()

        reservation_response = client.post(
            "/reservations",
            headers={
                "Authorization": f"Bearer {client_token}",
            },
            json={
                "restaurant_id": RESTAURANT_ID,
                "table_id": TABLE_ID,
                "reservation_date": date_string,
                "reservation_time": "19:00:00",
                "number_of_people": 2,
            },
        )

        if reservation_response.status_code == 201:
            return reservation_response.json()["id"]

        if reservation_response.status_code == 409:
            reservation_date += timedelta(days=1)
            continue

        assert reservation_response.status_code == 201, (
            reservation_response.json()
        )


def test_confirmed_reservation_creates_notification():

    # Connexion du client
    client_login = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )

    assert client_login.status_code == 200

    client_token = client_login.json()["access_token"]

    # Création d'une nouvelle réservation
    reservation_id = create_test_reservation(client_token)

    # Connexion du manager
    manager_login = client.post(
        "/auth/login",
        json={
            "email": "manager_test@example.com",
            "password": "Manager123!",
        },
    )

    assert manager_login.status_code == 200

    manager_token = manager_login.json()["access_token"]

    # Confirmation de la réservation
    status_response = client.patch(
        f"/reservations/{reservation_id}/status",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "status": "confirmed",
        },
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "confirmed"

    # Vérification de la notification du client
    notifications_response = client.get(
        "/notifications/me",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()

    matching_notifications = [
        notification
        for notification in notifications
        if notification["type"] == "reservation_confirmed"
        and notification["title"] == "Réservation confirmée"
    ]

    assert len(matching_notifications) >= 1
def test_client_can_delete_own_notification():
    # Connexion de l'admin
    admin_login = client.post(
        "/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "Admin123!",
        },
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    # Création d'une notification pour le client
    create_response = client.post(
        "/notifications",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "user_id": "b64bc08d-05b1-4cb9-a3ef-96f2682782a3",
            "title": "Notification à supprimer",
            "message": "Cette notification sera supprimée.",
            "type": "delete_test",
        },
    )

    assert create_response.status_code == 201

    notification_id = create_response.json()["id"]

    # Connexion du client
    client_login = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )
    assert client_login.status_code == 200
    client_token = client_login.json()["access_token"]

    # Suppression de sa propre notification
    delete_response = client.delete(
        f"/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {client_token}"},
    )

    assert delete_response.status_code == 204

    # Vérification que la notification n'est plus accessible
    get_response = client.get(
        f"/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {client_token}"},
    )

    assert get_response.status_code == 404
def test_client_cannot_delete_another_user_notification():
    # Connexion de l'admin
    admin_login = client.post(
        "/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "Admin123!",
        },
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    # Création d'une notification pour le manager
    create_response = client.post(
        "/notifications",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "user_id": "c6e46664-0a34-4766-9942-a5183e058e4f",
            "title": "Notification protégée",
            "message": "Cette notification appartient au manager.",
            "type": "delete_permission_test",
        },
    )

    assert create_response.status_code == 201

    notification_id = create_response.json()["id"]

    # Connexion du client
    client_login = client.post(
        "/auth/login",
        json={
            "email": "client_test@example.com",
            "password": "Client123!",
        },
    )
    assert client_login.status_code == 200
    client_token = client_login.json()["access_token"]

    # Le client essaie de supprimer la notification du manager
    delete_response = client.delete(
        f"/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {client_token}"},
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Notification introuvable."