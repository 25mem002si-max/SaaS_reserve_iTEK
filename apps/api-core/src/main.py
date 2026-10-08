from fastapi import FastAPI

from src.api.users import router as users_router
from src.api.auth import router as auth_router
from src.api.restaurants import router as restaurants_router
from src.api.restaurant_table import router as restaurant_tables_router
from src.api.reservations import router as reservations_router
from src.api.notifications import router as notifications_router
from src.api.payments import router as payments_router
from src.api.menu_categories import router as menu_categories_router



app = FastAPI(
    title="Restaurant SaaS API",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Restaurant SaaS API fonctionne !",
    }


app.include_router(users_router)
app.include_router(auth_router)
app.include_router(restaurants_router)
app.include_router(restaurant_tables_router)
app.include_router(reservations_router)
app.include_router(notifications_router)
app.include_router(payments_router)
app.include_router(menu_categories_router)