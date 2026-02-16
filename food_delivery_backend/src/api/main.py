from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.settings import get_settings
from src.api.db.init_db import create_all_tables, seed_data
from src.api.routes import auth, cart, orders, payments, realtime, restaurants

settings = get_settings()

openapi_tags = [
    {"name": "auth", "description": "Signup/login and user profile."},
    {"name": "restaurants", "description": "Browse restaurants and menus."},
    {"name": "cart", "description": "Manage cart items."},
    {"name": "orders", "description": "Create orders and track order lifecycle."},
    {"name": "payments", "description": "Payment intent/confirmation (mock provider)."},
    {"name": "realtime", "description": "WebSocket real-time order status updates."},
]


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for a food delivery platform.\n\n"
        "Real-time tracking:\n"
        "- WebSocket: connect to `/ws/orders/{order_id}` to receive order status events.\n"
        "- See `/realtime/help` for usage.\n"
    ),
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=settings.allowed_methods if settings.allowed_methods != ["*"] else ["*"],
    allow_headers=settings.allowed_headers if settings.allowed_headers != ["*"] else ["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables and seed minimal data on startup."""
    create_all_tables()
    seed_data()


@app.get("/", summary="Health Check")
def health_check():
    """Simple health check endpoint."""
    return {"message": "Healthy"}


app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(realtime.router)
