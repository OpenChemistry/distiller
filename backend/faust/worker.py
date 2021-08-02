import logging
from datetime import datetime
import aiohttp

import faust
from config import settings
from constants import (FILE_EVENT_TYPE_CLOSED, FILE_EVENT_TYPE_CREATED,
                       FILE_EVENT_TYPE_DELETED, TOPIC_FILE_EVENTS,
                       TOPIC_SCAN_EVENTS)
from schemas import ScanCreate, ScanUpdate
from utils import create_scan, extract_scan_id, get_scan, update_scan

# Setup logger
logger = logging.getLogger("worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "still", store="rocksdb://", broker=settings.KAFKA_URL, topic_partitions=1
)


class FileSystemEvent(faust.Record):
    event_type: str
    src_path: str
    is_directory: bool
    created: datetime


file_events_topic = app.topic(TOPIC_FILE_EVENTS, value_type=FileSystemEvent)


class ScanEvent(faust.Record):
    scan_id: int
    log_files: int


scan_events_topic = app.topic(TOPIC_SCAN_EVENTS, value_type=ScanEvent)


class LogFileState(faust.Record):
    received_created_event: bool = False
    received_closed_event: bool = False
    created: datetime = None
    processed: bool = False


log_files = app.Table("log_files", default=LogFileState)
scan_id_to_id = app.Table("scan_id_to_id", default=int)
scan_id_to_log_files = app.Table("scan_id_to_log_files", default=list)


def scan_complete(scan_log_files: List[str]):
    return len(scan_log_files) == 72

async def process_delete_event(path: str) -> None:
    scan_id = extract_scan_id(path)
    del log_files[path]
    scan_log_files = scan_id_to_log_files[scan_id]
    scan_log_files.remove(path)

    # If all the log file are gone then remove the scan
    if not scan_log_files:
        del scan_id_to_id[scan_id]
        del scan_id_to_log_files[scan_id]
        logger.info(f"Scan {scan_id} removed.")
    else:
        scan_id_to_log_files[scan_id] = scan_log_files


async def process_log_file(
    session: aiohttp.ClientSession, event: FileSystemEvent
) -> None:
    path = event.src_path
    scan_id = extract_scan_id(path)

    # If this is the first log file for the scan, issue an event
    if scan_id not in scan_id_to_log_files:
        scan_event = ScanEvent(scan_id, 0)
        await scan_events_topic.send(value=scan_event)
        scan = await create_scan(
            session, ScanCreate(scan_id=scan_id, created=event.created)
        )
        scan_id_to_id[scan_id] = scan.id

    # Update list of log file for the scan
    scan_log_files = scan_id_to_log_files[scan_id]
    scan_log_files.append(path)
    scan_log_files = set(scan_log_files)
    scan_id_to_log_files[scan_id] = scan_log_files

    scan_event = ScanEvent(scan_id, len(scan_log_files))
    await scan_events_topic.send(value=scan_event)

    if scan_id not in scan_id_to_id:
        scan = await get_scan(session, scan_id=scan_id, state="transfer")
        scan_id_to_id[scan_id] = scan.id

    await update_scan(
        session, ScanUpdate(id=scan_id_to_id[scan_id], log_files=len(scan_log_files))
    )

    if scan_complete(scan_log_files):
        logger.info(f"Transfer complete for scan {scan_id}")


@app.agent(file_events_topic)
async def watch_for_logs(file_events):
    async with aiohttp.ClientSession() as session:
        async for event in file_events:
            path = event.src_path
            event_type = event.event_type


            # Skip event we are not interested in
            if event_type not in [
                FILE_EVENT_TYPE_CREATED,
                FILE_EVENT_TYPE_CLOSED,
                FILE_EVENT_TYPE_DELETED,
            ]:
                continue

            # Handle delete
            if event_type == FILE_EVENT_TYPE_DELETED:
                await process_delete_event(path)
                continue

            # Check if we have already processed this log file.
            state = log_files[path]
            if state.processed and state.created == event.created:
                continue

            state.created = event.created
            if event_type == FILE_EVENT_TYPE_CREATED:
                state.received_created_event = True
            elif event_type == FILE_EVENT_TYPE_CLOSED:
                state.received_closed_event = True

            # We have seen the right events process the logfile
            if state.received_created_event and state.received_created_event:
                await process_log_file(session, event)

                state.processed = True

            # Ensure changelog is updated
            log_files[path] = state
