import asyncio

from aiokafka import AIOKafkaProducer

from app.schemas import FileSystemEvent


def serializer(event: FileSystemEvent) -> bytes:
    return event.json().encode()


producer = AIOKafkaProducer(
    loop=asyncio.get_event_loop(),
    bootstrap_servers="localhost:9092",
    value_serializer=serializer,
)


async def start():
    await producer.start()


async def stop():
    await producer.stop()


async def send_filesystem_event_to_kafka(event: FileSystemEvent) -> None:
    await producer.send("file_events", event)
