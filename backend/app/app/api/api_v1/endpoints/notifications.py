import asyncio
from typing import Any

from fastapi import APIRouter
from starlette.endpoints import WebSocketEndpoint

from app.kafka import consumer

router = APIRouter()

from fastapi import WebSocket


@router.websocket_route("/notifications")
class WebsocketConsumer(WebSocketEndpoint):
    async def on_connect(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        await self.websocket.accept()

        self.consumer = await consumer.create()
        self.relay_task = asyncio.create_task(self.relay_events())

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        self.relay_task.cancel()
        await self.consumer.stop()

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        # For now do nothing
        pass

    async def relay_events(self) -> None:
        try:
            async for msg in self.consumer:
                event = msg.value
                del event["__faust"]
                await self.websocket.send_json(event)
        finally:
            await self.consumer.stop()
