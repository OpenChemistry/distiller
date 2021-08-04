from fastapi import APIRouter, Depends
from fastapi.security.api_key import APIKey

from app import schemas
from app.api import deps
from app.kafka.producer import (send_filesystem_event_to_kafka,
                                send_sync_event_to_kafka)

router = APIRouter()


@router.post("")
async def file_events(
    event: schemas.FileSystemEvent, api_key: APIKey = Depends(deps.get_api_key)
):
    await send_filesystem_event_to_kafka(event)

    return event


@router.post("/sync")
async def file_events(
    event: schemas.SyncEvent, api_key: APIKey = Depends(deps.get_api_key)
):
    await send_sync_event_to_kafka(event)

    return event
