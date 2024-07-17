from typing import Union

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.core.constants import (TOPIC_CUSTODIAN_EVENTS,
                                TOPIC_HAADF_FILE_EVENTS,
                                TOPIC_JOB_CANCEL_EVENTS,
                                TOPIC_JOB_SUBMIT_EVENTS,
                                TOPIC_JOB_UPDATE_EVENTS,
                                TOPIC_MICROSCOPE_EVENTS, TOPIC_NOTEBOOK_EVENTS,
                                TOPIC_SCAN_EVENTS, TOPIC_SCAN_FILE_EVENTS,
                                TOPIC_SCAN_FILE_SYNC_EVENTS,
                                TOPIC_STATUS_FILE_EVENTS,
                                TOPIC_STATUS_FILE_SYNC_EVENTS)
from app.core.logging import logger
from app.schemas import (FileSystemEvent, HaadfUploaded, MicroscopeUpdateEvent,
                         NotebookCreateEvent, ScanCreatedEvent,
                         ScanFileUploaded, ScanUpdateEvent, SyncEvent)
from app.schemas.events import (CancelJobEvent, JobEventType,
                                RemoveScanFilesEvent, SubmitJobEvent,
                                UpdateJobEvent)


def serializer(event: FileSystemEvent) -> bytes:
    return event.json(exclude_none=True).encode()


producer = None


async def start():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=serializer,
        enable_idempotence=True,
        max_request_size=5242880, # 5MB
    )
    await producer.start()


async def stop():
    await producer.stop()


async def send_filesystem_event_to_kafka(event: FileSystemEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_STATUS_FILE_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_STATUS_FILE_EVENTS}")


async def send_log_file_sync_event_to_kafka(event: SyncEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_STATUS_FILE_SYNC_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_STATUS_FILE_SYNC_EVENTS}")


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


async def send_job_event_to_kafka(
    event: Union[SubmitJobEvent, CancelJobEvent, UpdateJobEvent]
) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")
    event_topic = {
        JobEventType.SUBMIT: TOPIC_JOB_SUBMIT_EVENTS,
        JobEventType.UPDATED: TOPIC_JOB_UPDATE_EVENTS,
        JobEventType.CANCEL: TOPIC_JOB_CANCEL_EVENTS,
    }
    if event.event_type not in event_topic:
        logger.exception(f"Topic not in event_topic map.")
        return
    topic = event_topic[event.event_type]

    try:
        await producer.send(topic, event)
    except:
        logger.exception(f"Exception send on topic: {topic}")


async def send_remove_scan_files_event_to_kafka(event: RemoveScanFilesEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_CUSTODIAN_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_CUSTODIAN_EVENTS}")


async def send_microscope_event_to_kafka(event: MicroscopeUpdateEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_MICROSCOPE_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_MICROSCOPE_EVENTS}")


async def send_notebook_event_to_kafka(event: NotebookCreateEvent) -> None:
    if producer is None:
        raise Exception("Producer has not been initialized")

    try:
        await producer.send(TOPIC_NOTEBOOK_EVENTS, event)
    except:
        logger.exception(f"Exception send on topic: {TOPIC_NOTEBOOK_EVENTS}")
