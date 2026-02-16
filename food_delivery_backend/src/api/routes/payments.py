import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db.models import Order, OrderStatus, PaymentIntent, PaymentStatus, User
from src.api.db.session import get_db
from src.api.deps import get_current_user
from src.api.realtime.broker import broker
from src.api.schemas import (
    ConfirmPaymentRequest,
    CreatePaymentIntentResponse,
    PaymentIntentOut,
)

router = APIRouter(prefix="/payments", tags=["payments"])


def _pi_out(pi: PaymentIntent) -> PaymentIntentOut:
    return PaymentIntentOut(
        id=pi.id,
        provider=pi.provider,
        client_secret=pi.client_secret,
        amount_cents=pi.amount_cents,
        currency=pi.currency,
        status=pi.status.value,
    )


@router.post(
    "/intent/{order_id}",
    response_model=CreatePaymentIntentResponse,
    summary="Create payment intent (mock)",
    description="Create (or return) a mock payment intent for an order. Marks order as PAYMENT_PENDING.",
)
async def create_payment_intent(
    order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CreatePaymentIntentResponse:
    order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == current_user.id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status in (OrderStatus.CANCELLED, OrderStatus.DELIVERED):
        raise HTTPException(status_code=400, detail="Cannot pay for this order")

    existing = db.scalar(select(PaymentIntent).where(PaymentIntent.order_id == order.id))
    if existing:
        return CreatePaymentIntentResponse(payment_intent=_pi_out(existing))

    client_secret = f"mock_{secrets.token_urlsafe(24)}"
    pi = PaymentIntent(
        order_id=order.id,
        provider="mock",
        client_secret=client_secret,
        amount_cents=order.total_cents,
        currency="usd",
        status=PaymentStatus.REQUIRES_CONFIRMATION,
    )
    db.add(pi)
    order.status = OrderStatus.PAYMENT_PENDING
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pi)

    await broker.publish_status(order.id, order.status.value)
    return CreatePaymentIntentResponse(payment_intent=_pi_out(pi))


@router.post(
    "/confirm/{order_id}",
    response_model=PaymentIntentOut,
    summary="Confirm payment (mock)",
    description="Confirm a mock payment by providing the client_secret. Marks payment SUCCEEDED and order CONFIRMED.",
)
async def confirm_payment(
    order_id: int,
    payload: ConfirmPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentIntentOut:
    order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == current_user.id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    pi = db.scalar(select(PaymentIntent).where(PaymentIntent.order_id == order.id))
    if not pi:
        raise HTTPException(status_code=400, detail="Payment intent not created")

    if payload.client_secret != pi.client_secret:
        pi.status = PaymentStatus.FAILED
        db.commit()
        raise HTTPException(status_code=400, detail="Payment confirmation failed")

    pi.status = PaymentStatus.SUCCEEDED
    order.status = OrderStatus.CONFIRMED
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pi)

    await broker.publish_status(order.id, order.status.value)
    return _pi_out(pi)
