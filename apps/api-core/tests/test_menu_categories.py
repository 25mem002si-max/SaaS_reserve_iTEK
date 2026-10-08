from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)

RESTAURANT_ID = "c6074aec-4f3c-45d5-9f11-b98379ab43a1"


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


def test_manager_can_create_menu_category():
    token = login_manager()

    category_name = f"Entrées Test {uuid4().hex[:8]}"

    response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "name": category_name,
            "description": "Catégorie créée par pytest.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == category_name
    assert data["description"] == "Catégorie créée par pytest."
    assert "id" in data
    assert "created_at" in data


def test_manager_can_list_restaurant_menu_categories():
    token = login_manager()

    response = client.get(
        f"/menu-categories/restaurant/{RESTAURANT_ID}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    category = next(
        (
            item
            for item in data
            if item["name"].startswith("Entrées Test")
        ),
        None,
    )

    assert category is not None
    assert category["restaurant_id"] == RESTAURANT_ID
def test_manager_can_get_menu_category():
    token = login_manager()

    list_response = client.get(
        f"/menu-categories/restaurant/{RESTAURANT_ID}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert list_response.status_code == 200

    categories = list_response.json()

    assert len(categories) >= 1

    category_id = categories[0]["id"]

    response = client.get(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["restaurant_id"] == RESTAURANT_ID
    assert "name" in data
    assert "description" in data
    assert "created_at" in data   
def test_manager_can_update_menu_category():
    token = login_manager()

    list_response = client.get(
        f"/menu-categories/restaurant/{RESTAURANT_ID}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert list_response.status_code == 200

    categories = list_response.json()

    assert len(categories) >= 1

    category = next(
        (
            item
            for item in categories
            if item["name"].startswith("Entrées Test")
        ),
        None,
    )

    assert category is not None

    category_id = category["id"]

    updated_name = f"Entrées Modifiées {uuid4().hex[:8]}"

    response = client.patch(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": updated_name,
            "description": "Description modifiée par pytest.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == updated_name
    assert data["description"] == "Description modifiée par pytest."   
def test_manager_can_delete_menu_category():
    token = login_manager()

    category_name = f"Catégorie Suppression {uuid4().hex[:8]}"

    create_response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "name": category_name,
            "description": "Catégorie créée pour tester la suppression.",
        },
    )

    assert create_response.status_code == 201

    category = create_response.json()

    category_id = category["id"]

    delete_response = client.delete(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Catégorie introuvable."
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


def test_client_cannot_create_menu_category():
    token = login_client()

    response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "name": f"Catégorie Client {uuid4().hex[:8]}",
            "description": "Cette catégorie ne doit pas être créée.",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Accès réservé aux managers et administrateurs."
    )
OTHER_RESTAURANT_ID = "4165d61d-fcf4-4332-bce4-a46c649f51d9"


def test_manager_cannot_create_category_for_other_restaurant():
    token = login_manager()

    response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": OTHER_RESTAURANT_ID,
            "name": f"Catégorie Non Autorisée {uuid4().hex[:8]}",
            "description": "Cette catégorie ne doit pas être créée.",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Vous n'êtes pas autorisé à gérer ce restaurant."
    ) 
def test_client_cannot_update_menu_category():
    manager_token = login_manager()

    list_response = client.get(
        f"/menu-categories/restaurant/{RESTAURANT_ID}",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
    )

    assert list_response.status_code == 200

    categories = list_response.json()
    assert len(categories) >= 1

    category = categories[0]
    category_id = category["id"]

    client_token = login_client()

    response = client.patch(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
        json={
            "name": f"Modification Client {uuid4().hex[:8]}",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Accès réservé aux managers et administrateurs."
    )  
def test_client_cannot_delete_menu_category():
    manager_token = login_manager()

    list_response = client.get(
        f"/menu-categories/restaurant/{RESTAURANT_ID}",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
    )

    assert list_response.status_code == 200

    categories = list_response.json()
    assert len(categories) >= 1

    category_id = categories[0]["id"]

    client_token = login_client()

    response = client.delete(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {client_token}",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Accès réservé aux managers et administrateurs."
 
   )  
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
def test_admin_can_create_menu_category():
    token = login_admin()

    category_name = f"Catégorie Admin {uuid4().hex[:8]}"

    response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "name": category_name,
            "description": "Catégorie créée par l'administrateur.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == category_name
    assert data["description"] == (
        "Catégorie créée par l'administrateur."
    )
    assert "id" in data
    assert "created_at" in data   
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


def test_admin_can_create_menu_category():
    token = login_admin()

    category_name = f"Catégorie Admin {uuid4().hex[:8]}"

    response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "name": category_name,
            "description": "Catégorie créée par l'administrateur.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == category_name
    assert data["description"] == (
        "Catégorie créée par l'administrateur."
    )
    assert "id" in data
    assert "created_at" in data
def test_admin_can_delete_menu_category():
    token = login_admin()

    category_name = f"Catégorie Admin Suppression {uuid4().hex[:8]}"

    create_response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "name": category_name,
            "description": "Catégorie créée pour tester la suppression Admin.",
        },
    )

    assert create_response.status_code == 201

    category = create_response.json()
    category_id = category["id"]

    delete_response = client.delete(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert get_response.status_code == 404

    assert get_response.json()["detail"] == (
        "Catégorie introuvable."
    )
def test_admin_can_delete_menu_category():
    token = login_admin()

    category_name = f"Catégorie Admin Suppression {uuid4().hex[:8]}"

    create_response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": RESTAURANT_ID,
            "name": category_name,
            "description": "Catégorie créée pour tester la suppression Admin.",
        },
    )

    assert create_response.status_code == 201

    category = create_response.json()
    category_id = category["id"]

    delete_response = client.delete(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert get_response.status_code == 404

    assert get_response.json()["detail"] == (
        "Catégorie introuvable."
    )
OTHER_RESTAURANT_ID = "4165d61d-fcf4-4332-bce4-a46c649f51d9"


def test_admin_can_manage_category_of_other_restaurant():
    token = login_admin()

    category_name = (
        f"Catégorie Admin Autre Restaurant {uuid4().hex[:8]}"
    )

    create_response = client.post(
        "/menu-categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "restaurant_id": OTHER_RESTAURANT_ID,
            "name": category_name,
            "description": "Catégorie gérée par l'administrateur.",
        },
    )

    assert create_response.status_code == 201

    category = create_response.json()

    assert category["restaurant_id"] == OTHER_RESTAURANT_ID
    assert category["name"] == category_name

    category_id = category["id"]

    update_response = client.patch(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": f"{category_name} Modifiée",
        },
    )

    assert update_response.status_code == 200

    updated_category = update_response.json()

    assert updated_category["id"] == category_id
    assert updated_category["restaurant_id"] == OTHER_RESTAURANT_ID
    assert updated_category["name"] == f"{category_name} Modifiée"

    delete_response = client.delete(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert delete_response.status_code == 204  
def test_admin_can_update_menu_category():
    admin_token = login_admin()

    list_response = client.get(
        f"/menu-categories/restaurant/{RESTAURANT_ID}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert list_response.status_code == 200

    categories = list_response.json()

    assert len(categories) >= 1

    category = categories[0]
    category_id = category["id"]

    updated_name = f"Catégorie Admin Modifiée {uuid4().hex[:8]}"

    response = client.patch(
        f"/menu-categories/{category_id}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "name": updated_name,
            "description": "Catégorie modifiée par l'administrateur.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == updated_name
    assert data["description"] == (
        "Catégorie modifiée par l'administrateur."
    )           