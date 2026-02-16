import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from src.api.schemas import OrderStatusEvent


class OrderEventBroker:
    """In-memory pub-sub for order status events per order_id."""

    def __init__(self) -> None:
        self._queues: dict[int, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, order_id: int) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._queues[order_id].add(q)
        return q

    async def unsubscribe(self, order_id: int, q: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self._queues[order_id].discard(q)
            if not self._queues[order_id]:
                self._queues.pop(order_id, None)

    async def publish_status(self, order_id: int, status: str) -> None:
        event = OrderStatusEvent(order_id=order_id, status=status, updated_at=datetime.now(timezone.utc)).model_dump()
        async with self._lock:
            queues = list(self._queues.get(order_id, set()))
        for q in queues:
            # best-effort, drop if slow consumer
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


broker = OrderEventBroker()
