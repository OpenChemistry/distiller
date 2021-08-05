import asyncio
import json

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.constants import TOPIC_SCAN_EVENTS


def deserializer(serialized):
    return json.loads(serialized)


async def create():
    loop = asyncio.get_event_loop()
    consumer = AIOKafkaConsumer(
        TOPIC_SCAN_EVENTS,
        loop=loop,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
        value_deserializer=deserializer,
    )

    await consumer.start()

    return consumer
