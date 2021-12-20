import logging
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

import aiohttp

import faust
from config import settings
from constants import (FILE_EVENT_TYPE_CLOSED, FILE_EVENT_TYPE_CREATED,
                       FILE_EVENT_TYPE_DELETED, FILE_EVENT_TYPE_MODIFIED,
                       LOG_PREFIX, PRIMARY_LOG_FILE_REGEX,
                       TOPIC_LOG_FILE_EVENTS, TOPIC_LOG_FILE_SYNC_EVENTS)
from schemas import Location, ScanCreate, ScanUpdate
from utils import (create_scan, delete_locations, extract_scan_id, get_scans,
                   update_scan)

# Setup logger
logger = logging.getLogger("scan_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller", store="rocksdb://", broker=settings.KAFKA_URL, topic_partitions=1
)


class FileSystemEvent(faust.Record):
    event_type: str
    src_path: str
    is_directory: bool
    created: Optional[datetime]
    host: str


file_events_topic = app.topic(TOPIC_LOG_FILE_EVENTS, value_type=FileSystemEvent)


class ScanEventType(str, Enum):
    CREATED = "scan.created"
    UPDATED = "scan.updated"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class File(faust.Record):
    path: str
    created: datetime
    host: str


class SyncEvent(faust.Record):
    files: List[File]


sync_events_topic = app.topic(TOPIC_LOG_FILE_SYNC_EVENTS, value_type=SyncEvent)


class LogFileState(faust.Record):
    created: datetime = None
    processed: bool = False
    host: str = None


# path to log file state
log_files = app.Table("log_files", default=LogFileState)
# native scan id to db id
scan_id_to_id = app.Table("scan_id_to_id", default=int)
# scan id to list of processed log files paths
scan_id_to_log_files = app.Table("scan_id_to_log_files", default=list)


def scan_complete(scan_log_files: List[str]):
    return len(scan_log_files) == 72


async def process_delete_event(session: aiohttp.ClientSession, path: str) -> None:
    scan_id = extract_scan_id(path)

    host = None
    if path in log_files:
        host = log_files[path].host
        del log_files[path]

    scan_log_files = scan_id_to_log_files[scan_id]
    # We are already done
    if not scan_log_files:
        return

    if path in scan_log_files:
        scan_log_files.remove(path)
        scan_id_to_log_files[scan_id] = scan_log_files

    # If all the log file are gone then remove the scan
    if not scan_log_files:
        id = scan_id_to_id[scan_id]
        del scan_id_to_id[scan_id]
        del scan_id_to_log_files[scan_id]
        logger.info(f"Scan {scan_id} removed.")
        if host is not None:
            logger.info(f"Delete all '{host}' locations for scan {id}")
            await delete_locations(session, id, host)


async def process_log_file(
    session: aiohttp.ClientSession, event: FileSystemEvent
) -> None:
    path = event.src_path
    scan_id = extract_scan_id(path)

    # Update list of log file for the scan
    scan_log_files = scan_id_to_log_files[scan_id]
    scan_log_files.append(path)
    scan_log_files = set(scan_log_files)
    scan_id_to_log_files[scan_id] = scan_log_files

    primary_log_file = re.match(PRIMARY_LOG_FILE_REGEX, path)

    # If this is the primary log file for the scan ( the one we use the timestamp from )
    # then check if we have a scan and create one if necessary
    if primary_log_file:
        # First check if we already have a scan
        scans = await get_scans(session, scan_id=scan_id, created=event.created)
        if len(scans) > 1:
            raise Exception("Multiple scans with the same id and creation time!")

        if len(scans) == 0:
            # We need get all paths
            paths = set()
            for log_file in scan_id_to_log_files[scan_id]:
                paths.add(str(Path(log_file).parent))

            locations = [Location(host=event.host, path=p) for p in paths]
            scan = await create_scan(
                session,
                ScanCreate(
                    scan_id=scan_id,
                    created=event.created,
                    logs_files=len(scan_id_to_log_files[scan_id]),
                    locations=locations,
                ),
            )
            scan_id_to_id[scan_id] = scan.id

            # Faust version
            locations = [Location(host=event.host, path=str(Path(path).parent))]
        else:
            scan = scans[0]
            scan_id_to_id[scan_id] = scan.id

    if scan_id in scan_id_to_id:
        locations = [Location(host=event.host, path=str(Path(path).parent))]
        await update_scan(
            session,
            ScanUpdate(
                id=scan_id_to_id[scan_id],
                log_files=len(scan_id_to_log_files[scan_id]),
                locations=locations,
            ),
        )

    if scan_complete(scan_id_to_log_files[scan_id]):
        logger.info(f"Transfer complete for scan {scan_id}")


def is_override(event: FileSystemEvent, state: LogFileState) -> bool:
    return state.created is not None and state.created != event.created


async def process_override(event: FileSystemEvent) -> None:
    scan_id = extract_scan_id(event.src_path)
    del scan_id_to_id[scan_id]
    del scan_id_to_log_files[scan_id]
    for p in log_files.keys():
        if scan_id == extract_scan_id(p):
            del log_files[p]


@app.agent(file_events_topic)
async def watch_for_logs(file_events):
    async with aiohttp.ClientSession() as session:
        async for event in file_events:
            path = event.src_path
            event_type = event.event_type

            # Only process log files
            if not Path(path).name.startswith(LOG_PREFIX):
                continue

            # Skip event we are not interested in
            if (
                event_type
                not in [
                    FILE_EVENT_TYPE_CREATED,
                    FILE_EVENT_TYPE_DELETED
                ]
                or event.is_directory
            ):
                continue

            # Handle delete
            if event_type == FILE_EVENT_TYPE_DELETED:
                await process_delete_event(session, path)
                continue

            # Check if we have already processed this log file.
            state = log_files[path]
            if state.processed and state.created == event.created:
                continue

            # We are seeing a scan being overridden
            if is_override(event, state):
                await process_override(event)

            state.created = event.created
            state.host = event.host

            # First set processed to True, otherwise another event for this
            # file could trigger double processing ...
            state.processed = True
            log_files[path] = state
            try:
                await process_log_file(session, event)
            except:
                # Reset the processed state
                state.processed = False
                log_files[path] = state
                raise

            # Ensure changelog is updated
            log_files[path] = state


async def process_sync_event(session: aiohttp.ClientSession, event: SyncEvent) -> None:
    # Handle deleted log files
    log_file_paths = [f.path for f in event.files]
    for f in log_files.keys():
        if f not in log_file_paths:
            await process_delete_event(f)

    for f in event.files:
        path = f.path
        state = log_files[f.path]

        # Only process log files
        if not Path(path).name.startswith(LOG_PREFIX):
            continue

        # Skip over anything that has already been proccessed
        if state.processed and state.created == f.created:
            continue

        file_event = FileSystemEvent(
            src_path=f.path,
            created=f.created,
            event_type=FILE_EVENT_TYPE_CREATED,
            is_directory=False,
            host=f.host,
        )
        # We are seeing a scan being overridden
        if is_override(file_event, state):
            await process_override(file_event)

        await process_log_file(session, file_event)

        state.created = f.created
        state.host = f.host
        state.received_created_event = True
        state.received_closed_event = True
        state.processed = True

        # Ensure changelog is updated
        log_files[path] = state


@app.agent(sync_events_topic)
async def watch_for_sync_event(sync_events):
    async with aiohttp.ClientSession() as session:
        async for event in sync_events:
            await process_sync_event(session, event)
