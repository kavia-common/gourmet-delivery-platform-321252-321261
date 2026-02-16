from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.api.db.models import CartItem, MenuItem, Order, OrderItem, OrderStatus, Restaurant, User
from src.api.db.session import get_db
from src.api.deps import get_current_user
from src.api.realtime.broker import broker
from src.api.schemas import CreateOrderResponse, OrderItemOut, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        restaurant_id=order.restaurant_id,
        status=order.status.value,
        subtotal_cents=order.subtotal_cents,
        delivery_fee_cents=order.delivery_fee_cents,
        total_cents=order.total_cents,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemOut(
                id=i.id,
                menu_item_id=i.menu_item_id,
                name=i.name,
                unit_price_cents=i.unit_price_cents,
                quantity=i.quantity,
                line_total_cents=i.line_total_cents,
            )
            for i in order.items
        ],
    )


@router.get(
    "",
    response_model=list[OrderOut],
    summary="List my orders",
    description="List orders for the authenticated user.",
)
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[OrderOut]:
    orders = (
        db.scalars(select(Order).where(Order.user_id == current_user.id).order_by(Order.id.desc()))
        .unique()
        .all()
    )
    # ensure items loaded
    for o in orders:
        _ = o.items
    return [_order_out(o) for o in orders]


@router.get(
    "/{order_id}",
    response_model=OrderOut,
    summary="Get order",
    description="Get a single order owned by the current user.",
)
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> OrderOut:
    order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == current_user.id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ = order.items
    return _order_out(order)


@router.post(
    "",
    response_model=CreateOrderResponse,
    summary="Create order from cart",
    description="Create an order from the current user's cart. All items must belong to the same restaurant.",
)
def create_order(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CreateOrderResponse:
    cart_items = db.scalars(select(CartItem).where(CartItem.user_id == current_user.id).order_by(CartItem.id)).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    menu_items = db.scalars(select(MenuItem).where(MenuItem.id.in_([ci.menu_item_id for ci in cart_items]))).all()
    if len(menu_items) != len(cart_items):
        raise HTTPException(status_code=400, detail="Cart contains invalid items")

    restaurant_ids = {mi.restaurant_id for mi in menu_items}
    if len(restaurant_ids) != 1:
        raise HTTPException(status_code=400, detail="All cart items must be from the same restaurant")
    restaurant_id = next(iter(restaurant_ids))

    restaurant = db.scalar(select(Restaurant).where(Restaurant.id == restaurant_id, Restaurant.is_active == True))  # noqa: E712
    if not restaurant:
        raise HTTPException(status_code=400, detail="Restaurant inactive or not found")

    # pricing
    by_id = {mi.id: mi for mi in menu_items}
    subtotal = 0
    order_items: list[OrderItem] = []
    for ci in cart_items:
        mi = by_id[ci.menu_item_id]
        line_total = mi.price_cents * ci.quantity
        subtotal += line_total
        order_items.append(
            OrderItem(
                menu_item_id=mi.id,
                name=mi.name,
                unit_price_cents=mi.price_cents,
                quantity=ci.quantity,
                line_total_cents=line_total,
            )
        )

    delivery_fee = 299 if subtotal < 3000 else 0
    total = subtotal + delivery_fee

    order = Order(
        user_id=current_user.id,
        restaurant_id=restaurant_id,
        status=OrderStatus.CREATED,
        subtotal_cents=subtotal,
        delivery_fee_cents=delivery_fee,
        total_cents=total,
        updated_at=datetime.utcnow(),
    )
    db.add(order)
    db.flush()
    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    # clear cart
    db.execute(delete(CartItem).where(CartItem.user_id == current_user.id))
    db.commit()
    db.refresh(order)
    _ = order.items

    return CreateOrderResponse(order=_order_out(order))


@router.post(
    "/{order_id}/status",
    response_model=OrderOut,
    summary="Advance order status (demo)",
    description="Advance order status forward for demo/testing. Only owner can call this.",
)
async def advance_status(
    order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> OrderOut:
    order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == current_user.id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    sequence = [
        OrderStatus.CREATED,
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.CONFIRMED,
        OrderStatus.PREPARING,
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.DELIVERED,
    ]
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot advance cancelled order")

    try:
        idx = sequence.index(order.status)
    except ValueError:
        idx = 0

    if idx >= len(sequence) - 1:
        return _order_out(order)

    order.status = sequence[idx + 1]
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    _ = order.items

    await broker.publish_status(order.id, order.status.value)
    return _order_out(order)
