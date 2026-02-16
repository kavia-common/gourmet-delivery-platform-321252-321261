from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.api.db.models import CartItem, MenuItem, User
from src.api.db.session import get_db
from src.api.deps import get_current_user
from src.api.schemas import CartItemIn, CartItemOut, CartOut, MenuItemOut

router = APIRouter(prefix="/cart", tags=["cart"])


def _cart_out(db: Session, user_id: int) -> CartOut:
    items = db.scalars(select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)).all()
    subtotal = 0
    out_items: list[CartItemOut] = []
    for ci in items:
        mi = db.scalar(select(MenuItem).where(MenuItem.id == ci.menu_item_id))
        if not mi:
            continue
        subtotal += mi.price_cents * ci.quantity
        out_items.append(
            CartItemOut(
                id=ci.id,
                quantity=ci.quantity,
                menu_item=MenuItemOut(
                    id=mi.id,
                    restaurant_id=mi.restaurant_id,
                    name=mi.name,
                    description=mi.description,
                    price_cents=mi.price_cents,
                ),
            )
        )
    return CartOut(items=out_items, subtotal_cents=subtotal)


@router.get(
    "",
    response_model=CartOut,
    summary="Get cart",
    description="Return current user's cart.",
)
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CartOut:
    return _cart_out(db, current_user.id)


@router.post(
    "/items",
    response_model=CartOut,
    summary="Add/update cart item",
    description="Add a menu item to cart or update its quantity.",
)
def upsert_cart_item(
    payload: CartItemIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    menu_item = db.scalar(select(MenuItem).where(MenuItem.id == payload.menu_item_id))
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    existing = db.scalar(
        select(CartItem).where(CartItem.user_id == current_user.id, CartItem.menu_item_id == payload.menu_item_id)
    )
    if existing:
        existing.quantity = payload.quantity
    else:
        db.add(CartItem(user_id=current_user.id, menu_item_id=payload.menu_item_id, quantity=payload.quantity))
    db.commit()
    return _cart_out(db, current_user.id)


@router.delete(
    "/items/{cart_item_id}",
    response_model=CartOut,
    summary="Remove cart item",
    description="Remove an item from cart.",
)
def remove_cart_item(
    cart_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    item = db.scalar(select(CartItem).where(CartItem.id == cart_item_id, CartItem.user_id == current_user.id))
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return _cart_out(db, current_user.id)


@router.delete(
    "",
    response_model=CartOut,
    summary="Clear cart",
    description="Remove all items from current user's cart.",
)
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CartOut:
    db.execute(delete(CartItem).where(CartItem.user_id == current_user.id))
    db.commit()
    return _cart_out(db, current_user.id)
