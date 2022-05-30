import re
from watchdog.events import FileSystemEvent
import asyncio
from typing import List

import aiohttp
import tenacity
from aiopath import AsyncPath
from pathlib import Path
from config import settings
from schemas import FileSystemEvent as FileSystemEventModel
from utils import logger
from watchdog.events import (EVENT_TYPE_MOVED, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED, FileSystemEvent)
from . import ModeHandler


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
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def upload_dm4(session: aiohttp.ClientSession, dm4_path: AsyncPath):
    logger.info(f"Uploading {dm4_path}")
    data = aiohttp.FormData()
    headers = {settings.API_KEY_NAME: settings.API_KEY}
    # We use the standard Path object here rather than the async version here,
    # as the AsyncPath performs very badly in our deployment (SL7). We can
    # probably revert this fix if/when we move away from SL7.
    with Path(dm4_path).open("rb") as fp:
        data.add_field(
            "file", fp, filename=dm4_path.name, content_type="application/octet-stream"
        )
        async with session.post(
            f"{settings.API_URL}/files/haadf", headers=headers, data=data
        ) as r:
            r.raise_for_status()

DM4_PATTERN = re.compile(r"^scan([0-9]*)\.dm4")
DM4_FILE_EVENTS = [EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED, EVENT_TYPE_MOVED]


class Scan4DHAADFFilesModeHandler(ModeHandler):
    async def on_event(self, event: FileSystemEvent):
        path = AsyncPath(event.src_path)

        # DM4 file case
        if event.event_type in DM4_FILE_EVENTS:
            # Could be a move event ( the microscopy software creates
            # a temp file and then moves it )
            if event.event_type == EVENT_TYPE_MOVED:
                path = AsyncPath(event.dest_path)

            # Check we are dealing with a DM4
            if DM4_PATTERN.match(path.name):
                await upload_dm4(self.session, path)