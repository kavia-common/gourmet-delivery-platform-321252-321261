from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db.models import MenuItem, Restaurant
from src.api.db.session import get_db
from src.api.schemas import MenuItemOut, RestaurantOut

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get(
    "",
    response_model=list[RestaurantOut],
    summary="List restaurants",
    description="List active restaurants.",
)
def list_restaurants(db: Session = Depends(get_db)) -> list[RestaurantOut]:
    rows = db.scalars(select(Restaurant).where(Restaurant.is_active == True).order_by(Restaurant.id)).all()  # noqa: E712
    return [RestaurantOut(id=r.id, name=r.name, description=r.description) for r in rows]


@router.get(
    "/{restaurant_id}/menu",
    response_model=list[MenuItemOut],
    summary="Get restaurant menu",
    description="List menu items for a given restaurant.",
)
def get_menu(restaurant_id: int, db: Session = Depends(get_db)) -> list[MenuItemOut]:
    restaurant = db.scalar(select(Restaurant).where(Restaurant.id == restaurant_id))
    if not restaurant or not restaurant.is_active:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items = db.scalars(select(MenuItem).where(MenuItem.restaurant_id == restaurant_id).order_by(MenuItem.id)).all()
    return [
        MenuItemOut(
            id=i.id,
            restaurant_id=i.restaurant_id,
            name=i.name,
            description=i.description,
            price_cents=i.price_cents,
        )
        for i in items
    ]
