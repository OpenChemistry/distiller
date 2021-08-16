import asyncio

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.core.constants import (TOPIC_HAADF_FILE_EVENTS, TOPIC_LOG_FILE_EVENTS,
                                TOPIC_LOG_FILE_SYNC_EVENTS, TOPIC_SCAN_EVENTS)
from app.schemas import (FileSystemEvent, HaadfUploaded, ScanHaadfUpdate,
                         SyncEvent)


def serializer(event: FileSystemEvent) -> bytes:
    return event.json().encode()


producer = AIOKafkaProducer(
    loop=asyncio.get_event_loop(),
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
    value_serializer=serializer,
)


async def start():
    await producer.start()


async def stop():
    await producer.stop()


async def send_filesystem_event_to_kafka(event: FileSystemEvent) -> None:
    await producer.send(TOPIC_LOG_FILE_EVENTS, event)


async def send_sync_event_to_kafka(event: SyncEvent) -> None:
    await producer.send(TOPIC_LOG_FILE_SYNC_EVENTS, event)


async def send_haadf_event_to_kafka(event: HaadfUploaded) -> None:
    await producer.send(TOPIC_HAADF_FILE_EVENTS, event)


async def send_scan_event_to_kafka(event: ScanHaadfUpdate) -> None:
    await producer.send(TOPIC_SCAN_EVENTS, event)
