import asyncio

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.core.constants import (TOPIC_HAADF_FILE_EVENTS, TOPIC_JOB_EVENTS,
                                TOPIC_LOG_FILE_EVENTS,
                                TOPIC_LOG_FILE_SYNC_EVENTS, TOPIC_SCAN_EVENTS, TOPIC_CUSTODIAN_EVENT)
from app.schemas import (FileSystemEvent, HaadfUploaded, ScanUpdateEvent,
                         SyncEvent)
from app.schemas.events import SubmitJobEvent
from app.core.logging import logger
from app.schemas.events import SubmitJobEvent, RemoveScanFilesEvent


def serializer(event: FileSystemEvent) -> bytes:
    return event.json(exclude_none=True).encode()


producer = None

async def start():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=serializer,
        enable_idempotence=True,
    )
    await producer.start()

async def stop():
    await producer.stop()


async def send_filesystem_event_to_kafka(event: FileSystemEvent) -> None:
    try:
        await producer.send(TOPIC_LOG_FILE_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_LOG_FILE_EVENTS}")



async def send_sync_event_to_kafka(event: SyncEvent) -> None:
    try:
        await producer.send(TOPIC_LOG_FILE_SYNC_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_LOG_FILE_SYNC_EVENTS}")


async def send_haadf_event_to_kafka(event: HaadfUploaded) -> None:
    try:
        await producer.send(TOPIC_HAADF_FILE_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_HAADF_FILE_EVENTS}")


async def send_scan_event_to_kafka(event: ScanUpdateEvent) -> None:
    try:
        await producer.send(TOPIC_SCAN_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_SCAN_EVENTS}")


async def send_submit_job_event_to_kafka(event: SubmitJobEvent) -> None:
    try:
        await producer.send(TOPIC_JOB_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_JOB_EVENTS}")


async def send_remove_scan_files_event_to_kafka(event: RemoveScanFilesEvent) -> None:
    try:
        await producer.send(TOPIC_CUSTODIAN_EVENT, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_CUSTODIAN_EVENT}")
