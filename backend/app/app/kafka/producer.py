import asyncio

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.schemas import FileSystemEvent, SyncEvent


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
    await producer.send("file_events", event)


async def send_sync_event_to_kafka(event: SyncEvent) -> None:
    await producer.send("file_sync_events", event)
