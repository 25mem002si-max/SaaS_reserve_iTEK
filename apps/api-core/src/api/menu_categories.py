
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.user import User
from src.schemas.menu_category import (
    MenuCategoryCreate,
    MenuCategoryResponse,
    MenuCategoryUpdate,
)
from src.security.auth import get_current_user
from src.services.menu_category_service import (
    create_menu_category,
    delete_menu_category,
    get_menu_category,
    get_restaurant_menu_categories,
    update_menu_category,
)


router = APIRouter(
    prefix="/menu-categories",
    tags=["Menu Categories"],
)


def get_current_manager_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in {
        UserRole.MANAGER.value,
        UserRole.ADMIN.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux managers et administrateurs.",
        )

    return current_user


@router.get(
    "/restaurant/{restaurant_id}",
    response_model=list[MenuCategoryResponse],
)
def list_menu_categories(
    restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_restaurant_menu_categories(
        db,
        restaurant_id,
    )


@router.get(
    "/{category_id}",
    response_model=MenuCategoryResponse,
)
def read_menu_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_menu_category(
        db,
        category_id,
    )


@router.post(
    "",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_category_endpoint(
    category_data: MenuCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin),
):
    return create_menu_category(
        db,
        category_data,
        current_user,
    )


@router.patch(
    "/{category_id}",
    response_model=MenuCategoryResponse,
)
def update_menu_category_endpoint(
    category_id: str,
    category_data: MenuCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin),
):
    return update_menu_category(
        db,
        category_id,
        category_data,
        current_user,
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu_category_endpoint(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin),
):
    delete_menu_category(
        db,
        category_id,
        current_user,
    )

    return None
