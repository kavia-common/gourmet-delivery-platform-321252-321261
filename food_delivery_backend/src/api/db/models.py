import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.api.db.base import Base


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_items")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "menu_item_id", name="uq_cart_user_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="cart_items")
    menu_item: Mapped["MenuItem"] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="RESTRICT"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False)

    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivery_fee_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="orders")
    restaurant: Mapped["Restaurant"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payment: Mapped["PaymentIntent | None"] = relationship(back_populates="order", cascade="all, delete-orphan", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")
    client_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="usd")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.REQUIRES_CONFIRMATION)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="payment")
