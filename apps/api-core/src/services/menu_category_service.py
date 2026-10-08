
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.enums.role import UserRole
from src.models.menu_category import MenuCategory
from src.models.restaurant import Restaurant
from src.models.user import User
from src.schemas.menu_category import (
    MenuCategoryCreate,
    MenuCategoryUpdate,
)


def verify_restaurant_access(
    db: Session,
    restaurant_id: str,
    current_user: User,
) -> Restaurant:
    restaurant = db.execute(
        select(Restaurant).where(
            Restaurant.id == restaurant_id
        )
    ).scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant introuvable.",
        )

    if current_user.role == UserRole.ADMIN.value:
        return restaurant

    if (
        current_user.role == UserRole.MANAGER.value
        and restaurant.manager_id == current_user.id
    ):
        return restaurant

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vous n'êtes pas autorisé à gérer ce restaurant.",
    )


def create_menu_category(
    db: Session,
    category_data: MenuCategoryCreate,
    current_user: User,
) -> MenuCategory:
    verify_restaurant_access(
        db,
        category_data.restaurant_id,
        current_user,
    )

    existing_category = db.execute(
        select(MenuCategory).where(
            MenuCategory.restaurant_id == category_data.restaurant_id,
            MenuCategory.name == category_data.name,
        )
    ).scalar_one_or_none()

    if existing_category is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette catégorie existe déjà pour ce restaurant.",
        )

    category = MenuCategory(
        restaurant_id=category_data.restaurant_id,
        name=category_data.name,
        description=category_data.description,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


def get_menu_category(
    db: Session,
    category_id: str,
) -> MenuCategory:
    category = db.execute(
        select(MenuCategory).where(
            MenuCategory.id == category_id
        )
    ).scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie introuvable.",
        )

    return category


def get_restaurant_menu_categories(
    db: Session,
    restaurant_id: str,
) -> list[MenuCategory]:
    restaurant = db.execute(
        select(Restaurant).where(
            Restaurant.id == restaurant_id
        )
    ).scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant introuvable.",
        )

    result = db.execute(
        select(MenuCategory)
        .where(
            MenuCategory.restaurant_id == restaurant_id
        )
        .order_by(
            MenuCategory.name.asc()
        )
    )

    return result.scalars().all()


def update_menu_category(
    db: Session,
    category_id: str,
    category_data: MenuCategoryUpdate,
    current_user: User,
) -> MenuCategory:
    category = get_menu_category(
        db,
        category_id,
    )

    verify_restaurant_access(
        db,
        category.restaurant_id,
        current_user,
    )

    if category_data.name is not None:
        existing_category = db.execute(
            select(MenuCategory).where(
                MenuCategory.restaurant_id == category.restaurant_id,
                MenuCategory.name == category_data.name,
                MenuCategory.id != category_id,
            )
        ).scalar_one_or_none()

        if existing_category is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cette catégorie existe déjà pour ce restaurant.",
            )

        category.name = category_data.name

    if category_data.description is not None:
        category.description = category_data.description

    db.commit()
    db.refresh(category)

    return category


def delete_menu_category(
    db: Session,
    category_id: str,
    current_user: User,
) -> None:
    category = get_menu_category(
        db,
        category_id,
    )

    verify_restaurant_access(
        db,
        category.restaurant_id,
        current_user,
    )

    db.delete(category)
    db.commit()
