from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db.base import Base
from src.api.db.models import MenuItem, Restaurant
from src.api.db.session import get_engine


# PUBLIC_INTERFACE
def create_all_tables() -> None:
    """Create all database tables (simple bootstrap, not a full migration system)."""
    Base.metadata.create_all(bind=get_engine())


def _seed_restaurants_if_empty(db: Session) -> None:
    existing = db.scalar(select(Restaurant.id).limit(1))
    if existing is not None:
        return

    r1 = Restaurant(name="Pasta Palace", description="Fresh pasta, fast delivery")
    r2 = Restaurant(name="Sushi Central", description="Rolls, nigiri, and sashimi")
    db.add_all([r1, r2])
    db.flush()

    db.add_all(
        [
            MenuItem(restaurant_id=r1.id, name="Spaghetti Carbonara", description="Classic creamy carbonara", price_cents=1499),
            MenuItem(restaurant_id=r1.id, name="Penne Arrabbiata", description="Spicy tomato sauce", price_cents=1299),
            MenuItem(restaurant_id=r2.id, name="Salmon Nigiri (6pc)", description="Fresh salmon nigiri", price_cents=1799),
            MenuItem(restaurant_id=r2.id, name="California Roll", description="Crab, avocado, cucumber", price_cents=1199),
        ]
    )


# PUBLIC_INTERFACE
def seed_data() -> None:
    """Seed minimal restaurants/menu items for local usage if DB is empty."""
    from src.api.db.session import SessionLocal

    db = SessionLocal()
    try:
        _seed_restaurants_if_empty(db)
        db.commit()
    finally:
        db.close()
