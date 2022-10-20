from typing import Union

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.core.constants import (TOPIC_CUSTODIAN_EVENT, TOPIC_HAADF_FILE_EVENTS,
                                TOPIC_JOB_EVENTS, TOPIC_LOG_FILE_EVENTS,
                                TOPIC_LOG_FILE_SYNC_EVENTS, TOPIC_SCAN_EVENTS,
                                TOPIC_SCAN_FILE_EVENTS,
                                TOPIC_SCAN_FILE_SYNC_EVENTS)
from app.core.logging import logger
from app.schemas import (FileSystemEvent, HaadfUploaded, ScanCreatedEvent,
                         ScanFileUploaded, ScanUpdateEvent, SyncEvent)
from app.schemas.events import RemoveScanFilesEvent, SubmitJobEvent


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
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_LOG_FILE_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_LOG_FILE_EVENTS}")


async def send_log_file_sync_event_to_kafka(event: SyncEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_LOG_FILE_SYNC_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_LOG_FILE_SYNC_EVENTS}")


async def send_scan_file_sync_event_to_kafka(event: SyncEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_SCAN_FILE_SYNC_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_SCAN_FILE_SYNC_EVENTS}")


async def send_haadf_event_to_kafka(event: HaadfUploaded) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_HAADF_FILE_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_HAADF_FILE_EVENTS}")


async def send_scan_file_event_to_kafka(event: ScanFileUploaded) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_SCAN_FILE_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_HAADF_FILE_EVENTS}")


async def send_scan_event_to_kafka(
    event: Union[ScanUpdateEvent, ScanCreatedEvent]
) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_SCAN_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_SCAN_EVENTS}")


async def send_submit_job_event_to_kafka(event: SubmitJobEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_JOB_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_JOB_EVENTS}")


async def send_remove_scan_files_event_to_kafka(event: RemoveScanFilesEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_CUSTODIAN_EVENT, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_CUSTODIAN_EVENT}")
