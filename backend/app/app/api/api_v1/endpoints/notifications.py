import asyncio
from contextlib import contextmanager
from typing import Any

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from starlette.endpoints import WebSocketEndpoint

from app.api.deps import get_current_user, get_db
from app.kafka import consumer
from app.core.logging import logger

router = APIRouter()

from fastapi import WebSocket


@router.websocket_route("/notifications")
class WebsocketConsumer(WebSocketEndpoint):
    relay_task = None
    consumer = None

    async def on_connect(self, websocket: WebSocket) -> None:
        try:
            self.websocket = websocket
            await self.websocket.accept()

            with contextmanager(get_db)() as db:
                await get_current_user(db, websocket.query_params.get("token"))

            self.consumer = await consumer.create()
            self.relay_task = asyncio.create_task(self.relay_events())
        except HTTPException as hex:
            if hex.status_code == status.HTTP_401_UNAUTHORIZED:
                await self.websocket.send_text(hex.detail)
                await self.websocket.close()
            else:
                raise

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if self.relay_task:
            self.relay_task.cancel()
        if self.consumer:
            await self.consumer.stop()

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        # For now do nothing
        pass

    async def relay_events(self) -> None:
        try:
            async for msg in self.consumer:
                event = msg.value
                try:
                    del event["__faust"]
                except KeyError:
                    pass
                await self.websocket.send_json(event)
        except:
            logger.exception("Exception relaying kafka message.")
        finally:
            await self.consumer.stop()
