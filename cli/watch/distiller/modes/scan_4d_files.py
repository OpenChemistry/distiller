import asyncio
import logging
import platform
import re
import signal
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import List, cast

import aiohttp
import coloredlogs
import tenacity
from aiopath import AsyncPath
from pathlib import Path
from aiowatchdog import AIOEventHandler, AIOEventIterator
from cachetools import TTLCache
from config import settings
from constants import STATUS_FILE_GLOB
from schemas import File, WatchMode
from schemas import FileSystemEvent as FileSystemEventModel
from schemas import SyncEvent
from watchdog.events import (EVENT_TYPE_DELETED, EVENT_TYPE_MODIFIED, EVENT_TYPE_CREATED,
                             EVENT_TYPE_MOVED, FileSystemEvent)
from utils import logger
from . import ModeHandler

STATUS_PATTERN = re.compile(r"^4dstem_rec_status_.*\.json")

STATUS_FILE_EVENTS = [EVENT_TYPE_CREATED, EVENT_TYPE_MOVED, EVENT_TYPE_MODIFIED, EVENT_TYPE_DELETED]

async def create_sync_snapshot(host, watch_dirs: List[str]) -> List[File]:
    files = []
    for watch_dir in watch_dirs:
        async for f in AsyncPath(watch_dir).glob(STATUS_FILE_GLOB):
            path = AsyncPath(f)
            stat_info = await path.stat()
            created = datetime.fromtimestamp(stat_info.st_ctime).astimezone()
            async with path.open('r') as fp:
                content = await fp.read()

            files.append(File(path=str(f), created=created, host=host, content=cast(str, content)))

    return files

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ) | tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ClientConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def post_sync_event(session: aiohttp.ClientSession, event: SyncEvent) -> None:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.post(
        f"{settings.API_URL}/files/sync", headers=headers, data=event.json()
    ) as r:
        r.raise_for_status()

        return await r.json()

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ) | tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ClientConnectionError
    ),

    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def post_file_event(
    session: aiohttp.ClientSession, event: FileSystemEventModel
) -> None:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.post(
        f"{settings.API_URL}/files", headers=headers, data=event.json()
    ) as r:
        r.raise_for_status()


class Scan4DFilesModeHandler(ModeHandler):
    def __init__(self, microscope_id: int,  host: str, session: aiohttp.ClientSession):
        super().__init__(microscope_id, host, session)

    async def on_event(self, event: FileSystemEvent):
        path = AsyncPath(event.src_path)
        event_type = event.event_type

        # We are only looking for status files
        if not (STATUS_PATTERN.match(path.name) and event_type in STATUS_FILE_EVENTS):
            return

        model = FileSystemEventModel(
            event_type=event.event_type,
            src_path=event.src_path,
            is_directory=event.is_directory,
            host=self.host,
        )

        if await path.exists():
            stat_info = await path.stat()
            model.created = datetime.fromtimestamp(stat_info.st_ctime).astimezone()

            # If its not a delete event attach the contents
            if event_type != EVENT_TYPE_DELETED:
                async with path.open('r') as fp:
                    content = await fp.read()
                    model.content = cast(str, content)

        def _log_exception(task: asyncio.Task) -> None:
            try:
                task.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Exception posting file event.")

        # Fire and forget
        task = asyncio.create_task(post_file_event(self.session, model))
        task.add_done_callback(_log_exception)

    async def sync(self):
        files = await create_sync_snapshot(self.host, settings.WATCH_DIRECTORIES)
        async with aiohttp.ClientSession() as session:
            await post_sync_event(session, SyncEvent(files=files))
