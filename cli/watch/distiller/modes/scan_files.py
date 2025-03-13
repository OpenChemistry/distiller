import asyncio
import re
from datetime import datetime
from typing import List, Optional, cast
import hashlib
import h5py


import aiohttp
import tenacity
from aiopath import AsyncPath
from pathlib import Path
from cachetools import TTLCache
from config import settings
from schemas import Location, ScanFromFileMetadata
from schemas import Scan
from utils import logger
from watchdog.events import (EVENT_TYPE_CLOSED, EVENT_TYPE_MODIFIED, EVENT_TYPE_CREATED,
                             EVENT_TYPE_MOVED, FileSystemEvent, FileMovedEvent)

from ncempy.io import emd

from . import ModeHandler



SCAN_FILE_GLOBS = ["*.dm4", "*.dm3", "*.emi", "*.emd"]
SCAN_FILE_PATTERNS = [re.compile(f"^.{g}") for g in SCAN_FILE_GLOBS]
SCAN_FILE_EVENTS = [EVENT_TYPE_CREATED, EVENT_TYPE_MOVED, EVENT_TYPE_MODIFIED, EVENT_TYPE_CLOSED]


def ser_file_path(emi_file_path: AsyncPath) -> AsyncPath:
    return emi_file_path.parent / f"{emi_file_path.stem}_1.ser"


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ) | tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ClientResponseError
    ) | tenacity.retry_if_exception_type(
        OSError
    ) | tenacity.retry_if_exception_type(
         asyncio.TimeoutError
    )
    ,
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def create_scan_from_file(microscope_id: int, host: str, session: aiohttp.ClientSession, scan_file_path: AsyncPath):
    logger.info(f"Uploading {scan_file_path}")
    data = aiohttp.FormData()
    headers = {settings.API_KEY_NAME: settings.API_KEY}
    # We use the standard Path object here rather than the async version here,
    # as the AsyncPath performs very badly in our deployment (SL7). We can
    # probably revert this fix if/when we move away from SL7.
    with Path(scan_file_path).open("rb") as fp:
        data.add_field("file", fp, filename=scan_file_path.name, content_type="application/octet-stream")

        ser_file = None
        try:
            # Special case for emi files, we need to also attach any associated ser file!
            if scan_file_path.suffix == '.emi':
                # Wait for ser file to appear
                tries = 5
                while tries > 0:
                    if await ser_file_path(scan_file_path).exists():
                        logger.info(f"Associated SER file found for: {scan_file_path}")
                        ser_file = Path(ser_file_path(scan_file_path)).open("rb")
                        name = f"{scan_file_path.stem}.ser"
                        data.add_field(name, ser_file, filename=name, content_type="application/octet-stream")
                        break
                    tries -= 1
                    await asyncio.sleep(1)

            # Add the metadata needed encoded in another field, we need to it this way as
            # we can have JSON and a file the same body ...
            location = Location(host=host, path=str(scan_file_path))
            stat_info = await scan_file_path.stat()
            metadata = ScanFromFileMetadata(microscope_id=microscope_id, created=datetime.fromtimestamp(stat_info.st_ctime).astimezone(), locations=[location])

            data.add_field(
                "scan_metadata", metadata.json(), content_type="application/json")

            async with session.post(
                f"{settings.API_URL}/scans", headers=headers, data=data
            ) as r:
                if r.status == 409:
                    logger.warning(f'"{scan_file_path}" has already been uploaded.')
                else:
                    r.raise_for_status()
        finally:
            if ser_file is not None:
                ser_file.close()

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def get_scans(
    session: aiohttp.ClientSession,
    sha: Optional[str] = None,
) -> List[Scan]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    params = {}
    if sha is not None:
        params["sha"] = sha

    async with session.get(
        f"{settings.API_URL}/scans", headers=headers, params=params
    ) as r:
        r.raise_for_status()
        json = await r.json()

        return [Scan(**x) for x in json]


class ScanFilesModeHandler(ModeHandler):
    def __init__(self, microscope_id: int,  host: str, session: aiohttp.ClientSession):
        super().__init__(microscope_id, host, session)
        self._cache = TTLCache(maxsize=100000, ttl=5*60)

    async def _handle_emd(self, event: FileSystemEvent):
        if event.event_type in [EVENT_TYPE_CREATED, EVENT_TYPE_MOVED, EVENT_TYPE_MODIFIED]:
            try:

                # Retry logic for PermissionError
                for attempt in tenacity.Retrying(wait=tenacity.wait_fixed(1),
                                                 stop=tenacity.stop_after_attempt(10),
                                                 retry=tenacity.retry_if_exception_type(PermissionError)):
                    with attempt:
                        if not h5py.is_hdf5(event.src_path):
                            return

                with emd.fileEMD(event.src_path, readonly=True) as emd_file:
                    if len(emd_file.list_emds) > 0:
                        path = AsyncPath(event.src_path)
                        await create_scan_from_file(self.microscope_id, self.host, self.session, path)
                        key = event.src_path
                        self._cache[key] = True
            except Exception:
                logger.exception("Error reading EMD")

    async def on_event(self, event: FileSystemEvent):
        path = AsyncPath(event.src_path)

        pattern_match = False
        for pattern in SCAN_FILE_PATTERNS:
            if pattern.match(path.name):
                pattern_match = True
                break

        if event.event_type not in SCAN_FILE_EVENTS or not pattern_match:
            return

        key = event.src_path
        # Handle EMD, we need to make sure it a complete file
        if path.suffix.lower() == ".emd" and key not in self._cache:
            await self._handle_emd(event)
            return

        # Could be a move event ( the microscopy software creates
        # a temp file and then moves it )
        if event.event_type == EVENT_TYPE_MOVED:
            path = AsyncPath(cast(FileMovedEvent, event).dest_path)

        if key in self._cache:
            return

        await create_scan_from_file(self.microscope_id, self.host, self.session, path)

        self._cache[key] = True

    def  generate_sha256(self, path: str, created: datetime):
        sha = hashlib.sha256()
        sha.update(self.host.encode())
        sha.update(path.encode())
        sha.update(created.isoformat().encode())
        sha.update(str(self.microscope_id).encode())

        return sha.hexdigest()

    async def sync(self):
        files = []
        for watch_dir in settings.WATCH_DIRECTORIES:
            for g in SCAN_FILE_GLOBS:
                async for f in AsyncPath(watch_dir).glob(f"**/{g}"):
                    path = AsyncPath(f)
                    stat_info = await path.stat()
                    created = datetime.fromtimestamp(stat_info.st_ctime).astimezone()
                    sha = self.generate_sha256(str(path), created)
                    # See if we already have a scan for this sha
                    scans = await get_scans(self.session, sha)
                    if len(scans) == 0:
                        # Create new scan from file
                        await create_scan_from_file(self.microscope_id, self.host, self.session, path)
                    else:
                        logger.info(f"Skipping '{path}' scan already exists")