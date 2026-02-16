import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.realtime.broker import broker

router = APIRouter(tags=["realtime"])


@router.get(
    "/realtime/help",
    summary="Real-time tracking help",
    description="Explains how to connect to WebSocket order tracking.",
)
def realtime_help():
    return {
        "websocket": {
            "url": "/ws/orders/{order_id}",
            "messages": "Server sends JSON OrderStatusEvent whenever status changes.",
            "example_event": {"order_id": 123, "status": "PREPARING", "updated_at": "2026-01-01T00:00:00Z"},
        }
    }


@router.websocket("/ws/orders/{order_id}")
async def ws_order_status(websocket: WebSocket, order_id: int):
    """
    WebSocket endpoint to receive real-time order status updates.

    - Connect to `/ws/orders/{order_id}`.
    - The server pushes JSON events whenever the order status changes.
    - This is an unauthenticated channel in this implementation (demo). If needed, add JWT token via query param/header.
    """
    await websocket.accept()
    q = await broker.subscribe(order_id)
    try:
        while True:
            # send next event, also keep connection alive
            try:
                event = await asyncio.wait_for(q.get(), timeout=25.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        await broker.unsubscribe(order_id, q)
