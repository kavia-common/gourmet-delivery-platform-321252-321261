from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: Literal["bearer"] = Field(default="bearer", description="Token type")


class SignupRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserOut(BaseModel):
    id: int = Field(..., description="User id")
    email: str = Field(..., description="User email")


class RestaurantOut(BaseModel):
    id: int = Field(..., description="Restaurant id")
    name: str = Field(..., description="Restaurant name")
    description: str | None = Field(None, description="Restaurant description")


class MenuItemOut(BaseModel):
    id: int = Field(..., description="Menu item id")
    restaurant_id: int = Field(..., description="Restaurant id")
    name: str = Field(..., description="Item name")
    description: str | None = Field(None, description="Item description")
    price_cents: int = Field(..., ge=0, description="Item price in cents")


class CartItemIn(BaseModel):
    menu_item_id: int = Field(..., description="Menu item id")
    quantity: int = Field(..., ge=1, le=50, description="Quantity (1-50)")


class CartItemOut(BaseModel):
    id: int = Field(..., description="Cart item id")
    menu_item: MenuItemOut = Field(..., description="Menu item")
    quantity: int = Field(..., ge=1, description="Quantity")


class CartOut(BaseModel):
    items: list[CartItemOut] = Field(..., description="Items in cart")
    subtotal_cents: int = Field(..., ge=0, description="Subtotal in cents")


class OrderItemOut(BaseModel):
    id: int = Field(..., description="Order item id")
    menu_item_id: int = Field(..., description="Menu item id")
    name: str = Field(..., description="Item name (snapshot)")
    unit_price_cents: int = Field(..., ge=0, description="Unit price in cents")
    quantity: int = Field(..., ge=1, description="Quantity")
    line_total_cents: int = Field(..., ge=0, description="Line total in cents")


class OrderOut(BaseModel):
    id: int = Field(..., description="Order id")
    restaurant_id: int = Field(..., description="Restaurant id")
    status: str = Field(..., description="Order status")
    subtotal_cents: int = Field(..., ge=0, description="Subtotal")
    delivery_fee_cents: int = Field(..., ge=0, description="Delivery fee")
    total_cents: int = Field(..., ge=0, description="Total")
    created_at: datetime = Field(..., description="Created time")
    updated_at: datetime = Field(..., description="Updated time")
    items: list[OrderItemOut] = Field(..., description="Order items")


class CreateOrderResponse(BaseModel):
    order: OrderOut = Field(..., description="Created order")


class PaymentIntentOut(BaseModel):
    id: int = Field(..., description="Payment intent id")
    provider: str = Field(..., description="Payment provider")
    client_secret: str = Field(..., description="Client secret (mock)")
    amount_cents: int = Field(..., ge=0, description="Amount in cents")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Payment status")


class CreatePaymentIntentResponse(BaseModel):
    payment_intent: PaymentIntentOut = Field(..., description="Created payment intent")


class ConfirmPaymentRequest(BaseModel):
    client_secret: str = Field(..., description="Client secret to confirm")


class OrderStatusEvent(BaseModel):
    order_id: int = Field(..., description="Order id")
    status: str = Field(..., description="New status")
    updated_at: datetime = Field(..., description="Update time")
