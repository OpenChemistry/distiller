import asyncio
from contextlib import contextmanager
from typing import Any

from cachetools import LRUCache
from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from starlette.endpoints import WebSocketEndpoint

from app.api.deps import get_current_user, get_db
from app.core.logging import logger
from app.crud import scan as scan_crud
from app.kafka import consumer
from app.schemas.microscope import MicroscopeEventType

router = APIRouter()

from fastapi import WebSocket

# Cache map of scan ids to microscope ids for filtering
scan_id_to_microscope_id = LRUCache(maxsize=1000)


def get_microscope_id_by_scan_id(db: Session, scan_id: int):
    if scan_id in scan_id_to_microscope_id:
        return scan_id_to_microscope_id[scan_id]

    scan = scan_crud.get_scan(db, scan_id)
    scan_id_to_microscope_id[scan_id] = scan.microscope_id

    return scan.microscope_id


@router.websocket_route("/notifications")
class WebsocketConsumer(WebSocketEndpoint):
    relay_task = None
    consumer = None

    async def on_connect(self, websocket: WebSocket) -> None:
        try:
            self.websocket = websocket
            await self.websocket.accept()

            self.microscope_id = int(websocket.query_params.get("microscope_id"))

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
        if self.consumer is None:
            raise Exception(
                "on_connect has not been called, consumer is not initialized"
            )

        try:
            async for msg in self.consumer:
                event = msg.value
                try:
                    del event["__faust"]
                except KeyError:
                    pass

                microscope_id = None
                if "microscope_id" in event:
                    microscope_id = event["microscope_id"]
                elif event.get("event_type") == MicroscopeEventType.UPDATED:
                    microscope_id = event["id"]
                elif "id" in event:
                    with contextmanager(get_db)() as db:
                        microscope_id = get_microscope_id_by_scan_id(db, event["id"])

                # Only send the message for the associated microscope
                if microscope_id is None or microscope_id == self.microscope_id:
                    await self.websocket.send_json(event)
        except asyncio.CancelledError:
            logger.info("Websocket connection closed, relay_events task cancelled")
        except Exception as e:
            logger.exception("Exception relaying kafka message: %s", str(e))
        finally:
            await self.consumer.stop()
