import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import pytz
from pydantic.error_wrappers import ValidationError

import faust
from config import settings
from constants import (FILE_EVENT_TYPE_CREATED, FILE_EVENT_TYPE_DELETED,
                       FILE_EVENT_TYPE_MODIFIED, PRIMARY_STATUS_FILE_REGEX,
                       STATUS_PREFIX, TOPIC_SCAN_METADATA_EVENTS,
                       TOPIC_STATUS_FILE_EVENTS, TOPIC_STATUS_FILE_SYNC_EVENTS)
from faust_records import ScanMetadata
from schemas import Location, ScanCreate, ScanStatusFile, ScanUpdate
from utils import (create_scan, delete_locations, extract_scan_id, get_scan,
                   get_scans, update_scan)

# Setup logger
logger = logging.getLogger("scan_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller-scan", store="rocksdb://", broker=settings.KAFKA_URL, topic_partitions=1
)


class FileSystemEvent(faust.Record):
    event_type: str
    src_path: str
    is_directory: bool
    created: Optional[datetime]
    host: str
    content: Optional[str]


file_events_topic = app.topic(TOPIC_STATUS_FILE_EVENTS, value_type=FileSystemEvent)


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
    content: str


class SyncEvent(faust.Record):
    files: List[File]


sync_events_topic = app.topic(TOPIC_STATUS_FILE_SYNC_EVENTS, value_type=SyncEvent)


class ScanStatus(faust.Record, coerce=True):
    created: Optional[str] = None
    uuid: Optional[str] = None
    host: Optional[str] = None
    paths: List[str] = []
    # map of path to progress for receiver
    progress_by_path: Dict[str, int] = None
    modified: Optional[datetime] = None

    def progress(self):
        return round(sum(self.progress_by_path.values())/4)

# native scan id to distiller id
scan_id_to_distiller_id = app.Table("scan_id_to_id", default=int)
# scan_id to status
scan_id_to_status = app.Table("status", default=ScanStatus)
# scan_id to metadata
scan_id_to_metadata = app.Table("metadata", default=None)
# path to uuid
path_to_uuid = app.Table("uuid", default=str)


def purge_scan_metadata(scan_id: int):
    if scan_id in scan_id_to_metadata:
        del scan_id_to_metadata[scan_id]


def purge_scan_data(scan_id):
    if scan_id in scan_id_to_distiller_id:
        del scan_id_to_distiller_id[scan_id]

    if scan_id in scan_id_to_status:
        status = scan_id_to_status[scan_id]
        for p in status.paths:
            del path_to_uuid[p]

        del scan_id_to_status[scan_id]

    purge_scan_metadata(scan_id)


def reap_scan_metadata():
    for (key, record) in scan_id_to_metadata.items():
        expiration = timedelta(hours=1)
        now = datetime.utcnow()
        if now - record.created > expiration:
            purge_scan_metadata(key)


def reap_scan_status():
    for (key, record) in scan_id_to_status.items():
        expiration = timedelta(hours=1)
        now = datetime.utcnow()
        if (
            key not in scan_id_to_distiller_id
            and record.modified is not None
            and now - record.modified > expiration
        ):
            purge_scan_data(key)


async def process_delete_event(session: aiohttp.ClientSession, path: str) -> None:
    scan_id = extract_scan_id(path)
    distiller_id = None
    host = None

    # Has the scan already been cleaned up?
    if (
        scan_id not in scan_id_to_distiller_id
        and scan_id not in scan_id_to_status
        and scan_id not in scan_id_to_metadata
    ):
        return

    if scan_id in scan_id_to_distiller_id:
        distiller_id = scan_id_to_distiller_id[scan_id]

    # Clean up scan_status
    if scan_id in scan_id_to_status:
        status = scan_id_to_status[scan_id]
        host = status.host
        purge_scan_data(scan_id)

    logger.info(f"Scan {scan_id} removed.")
    if host is not None and distiller_id is not None:
        logger.info(f"Delete all '{host}' locations for scan {distiller_id}")
        await delete_locations(session, distiller_id, host)


latest_scan_uuid = None


async def process_status_file(
    session: aiohttp.ClientSession, event: FileSystemEvent
) -> None:
    path = event.src_path

    # Get the status file content
    if event.content is None:
        raise Exception("Status file not included!")

    status_file = ScanStatusFile.parse_raw(event.content)
    scan_id = status_file.last_scan_number
    new_scan = scan_id not in scan_id_to_distiller_id
    primary_status_file = (
        re.match(PRIMARY_STATUS_FILE_REGEX, Path(path).name) is not None
    )
    distiller_id = None
    progress_updated = False
    scan_create = False

    # First update the scan status in our table
    scan_status = scan_id_to_status[scan_id]
    scan_status.modified = datetime.utcnow()

    if path not in scan_status.progress_by_path or scan_status.progress_by_path[path] < status_file.progress:
        scan_status.progress_by_path[path] = status_file.progress
        progress_updated = True
    scan_status.host = event.host
    paths = set(scan_status.paths)
    paths.add(path)
    scan_status.paths = paths
    if primary_status_file:
        scan_status.uuid = status_file.uuid
        scan_status.created = status_file.time
    scan_id_to_status[scan_id] = scan_status

    # Save the uuid, so we detect if we have an override
    path_to_uuid[path] = status_file.uuid

    # The global storing the uuid of the last scan we created
    global latest_scan_uuid

    # We have a new scan
    if new_scan and primary_status_file:
        # Special case for a current scan that has been deleted. The receiver
        # processes will still write to the status files so we will still get
        # events. We don't want to recreate the scan so we save the uuid of the
        # last scan we created. If the uuid's match we can just skip over the
        # events
        if scan_status.uuid == latest_scan_uuid:
            return

        # First check if we already have a scan
        scans = await get_scans(session, scan_id=scan_id, uuid=status_file.uuid)

        if len(scans) > 1:
            raise Exception("Multiple scans with the same id and creation time!")

        if len(scans) == 0:
            paths = set()
            for path in scan_status.paths:
                paths.add(str(Path(path).parent))

            locations = [Location(host=event.host, path=p) for p in paths]

            metadata = None
            if scan_id in scan_id_to_metadata:
                metadata = scan_id_to_metadata[scan_id].metadata

            scan = await create_scan(
                session,
                ScanCreate(
                    scan_id=scan_id,
                    uuid=scan_status.uuid,
                    created=scan_status.created,
                    progress=scan_status.progress(),
                    locations=locations,
                    metadata=metadata,
                ),
            )
            # Update our uuid for the latest scan
            latest_scan_uuid = scan_status.uuid
            scan_create = True
            scan_id_to_distiller_id[scan_id] = scan.id
            purge_scan_metadata(scan_id)

            # Faust version
            locations = [Location(host=event.host, path=str(Path(path).parent))]
        else:
            scan = scans[0]
            scan_id_to_distiller_id[scan_id] = scan.id

        distiller_id = scan.id

    # We have an existing scan
    elif not new_scan:
        distiller_id = scan_id_to_distiller_id[scan_id]

    if distiller_id is not None:
        locations = [Location(host=event.host, path=str(Path(path).parent))]
        try:
            await update_scan(
                session,
                ScanUpdate(
                    id=distiller_id,
                    progress=scan_status.progress(),
                    locations=locations,
                ),
            )
        except aiohttp.client_exceptions.ClientResponseError as ex:
            if ex.code == 404:
                logger.info(f"Scan '{distiller_id}' have been remove, skipping update.")
                return

            raise

    if (scan_status.progress() == 100 and scan_create) or (
        distiller_id is not None and progress_updated and scan_status.progress() == 100
    ):
        logger.info(f"Transfer complete for scan {scan_id}")


def is_override(path: str, uuid: str) -> bool:
    return path in path_to_uuid and path_to_uuid[path] != uuid


async def process_override(status_file: ScanStatusFile) -> None:
    scan_id = status_file.last_scan_number
    logger.info(f"Processing override for: {scan_id}")
    purge_scan_data(scan_id)


@app.agent(file_events_topic)
async def watch_for_event(file_events):
    global latest_scan_uuid

    async with aiohttp.ClientSession() as session:
        # initialize the scan uuid for the last scan we have created
        scans = await get_scans(session, microscope_id=1, limit=1)

        if len(scans) != 1:
            raise Exception("Unable to fetch latest scan uuid")

        latest_scan_uuid = scans[0].uuid

        logger.info(f"Last scan uuid: {latest_scan_uuid}")

        async for event in file_events:
            reap_scan_metadata()
            reap_scan_status()

            path = event.src_path
            event_type = event.event_type

            # Only process status files and data files
            if Path(path).suffix not in [".json"]:
                continue

            # Skip event we are not interested in
            if (
                event_type
                not in [
                    FILE_EVENT_TYPE_CREATED,
                    FILE_EVENT_TYPE_MODIFIED,
                    FILE_EVENT_TYPE_DELETED,
                ]
                or event.is_directory
            ):
                continue

            # Handle delete
            if event_type == FILE_EVENT_TYPE_DELETED:
                await process_delete_event(session, path)
                continue

            # Get the status file content
            if event.content is None:
                raise Exception("Status file not included!")

            try:
                status_file = ScanStatusFile.parse_raw(event.content)
            except ValidationError:
                logger.warning(f"Skipping {path}, with validation error.")
                continue

            # We are seeing a scan being overridden
            if is_override(path, status_file.uuid):
                await process_override(status_file)

            await process_status_file(session, event)


async def process_sync_event(session: aiohttp.ClientSession, event: SyncEvent) -> None:
    # Handle deleted log files
    status_file_paths = [f.path for f in event.files]
    for f in path_to_uuid.keys():
        if f not in status_file_paths:
            await process_delete_event(session, f)

    for f in event.files:
        path = f.path

        # Only process log files
        if not Path(path).name.startswith(STATUS_PREFIX):
            continue

        file_event = FileSystemEvent(
            src_path=path,
            created=f.created,
            event_type=FILE_EVENT_TYPE_CREATED,
            is_directory=False,
            host=f.host,
            content=f.content,
        )

        try:
            status = ScanStatusFile.parse_raw(f.content)
        except ValidationError:
            logger.warning(f"Skipping {path}, with validation error.")
            continue

        # We are seeing a scan being overridden
        if is_override(path, status.uuid):
            await process_override(status)

        await process_status_file(session, file_event)


@app.agent(sync_events_topic)
async def watch_for_sync_event(sync_events):
    async with aiohttp.ClientSession() as session:
        async for event in sync_events:
            await process_sync_event(session, event)


class ScanMetadataExpirableRecord(faust.Record, coerce=True):
    created: datetime
    metadata: Dict[str, Any]


scan_metadata_events_topic = app.topic(
    TOPIC_SCAN_METADATA_EVENTS, value_type=ScanMetadata
)


@app.agent(scan_metadata_events_topic)
async def watch_for_metadata_event(metadata_events):
    async with aiohttp.ClientSession() as session:
        async for event in metadata_events:
            reap_scan_metadata()
            scan_id = event.scan_id
            metadata = event.metadata

            # If we already have scan for this metadata we can attach it to this
            # scan.
            if scan_id in scan_id_to_distiller_id:
                id = scan_id_to_distiller_id[scan_id]
                scan = await get_scan(session, id)

                current_time = datetime.utcnow()
                created_since = current_time - timedelta(
                    hours=settings.HAADF_METADATA_SCAN_AGE_LIMIT
                )

                # Get created time in UTC without timezone info so we can compare
                created_utc = scan.created.astimezone(pytz.utc).replace(tzinfo=None)
                if created_utc > created_since:
                    # Update the scans metadata
                    await update_scan(session, ScanUpdate(id=id, metadata=metadata))
                else:
                    logger.warn(
                        f"Skipping associated metadata with scan {id} at the scan was created outside the window."
                    )
                    continue
            # Save the metadata so we can used it when we create a scan
            else:
                scan_id_to_metadata[scan_id] = ScanMetadataExpirableRecord(
                    created=datetime.utcnow(), metadata=metadata
                )
