import asyncio
import re
from datetime import datetime, timedelta
from typing import List, cast
import os
import shutil

import aiohttp
import tenacity
from aiopath import AsyncPath
from config import settings
from constants import STATUS_FILE_GLOB
from schemas import (File, FileSystemEvent as FileSystemEventModel, SyncEvent,
    ScanStatusFile, MicroscopeUpdate )

from watchdog.events import (EVENT_TYPE_DELETED, EVENT_TYPE_MODIFIED, EVENT_TYPE_CREATED,
                             EVENT_TYPE_MOVED, FileSystemEvent, FileCreatedEvent)
from utils import logger, get_microscope_by_id
from . import ModeHandler

STATUS_PATTERN = re.compile(r"^4dstem_rec_status_([0-3]{1}).*\.json")

STATUS_FILE_EVENTS = [EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED, EVENT_TYPE_DELETED, EVENT_TYPE_MOVED]

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

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ) | tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ClientConnectionError
    ),

    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def patch_microscope(
    session: aiohttp.ClientSession, id: int, update: MicroscopeUpdate
) -> None:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.patch(
        f"{settings.API_URL}/microscopes/{id}", headers=headers, data=update.json()
    ) as r:
        r.raise_for_status()

def find_mount_point(path):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path

class Scan4DFilesModeHandler(ModeHandler):
    def __init__(self, microscope_id: int,  host: str, session: aiohttp.ClientSession):
        super().__init__(microscope_id, host, session)
        self._receiver_progress = {}

        # File mounts point to use for calculating disk usage
        self._mount_points = set()
        for d in settings.WATCH_DIRECTORIES:
             self._mount_points.add(find_mount_point(d))


    async def _send_disk_usage(self, path: str):
        # First get the current microscope state
        microscope = await get_microscope_by_id(self.session, self.microscope_id)
        state = microscope.state if microscope.state is not None else {}
        disk_usage = state.setdefault("disk_usage", {})
        state_total = disk_usage.get("total")
        state_used = disk_usage.get("used")
        state_free = disk_usage.get("free")

        # Iterate over mount points and calculate the disk usage
        total = 0
        used = 0
        free = 0
        for p in self._mount_points:
            (total_, used_, free_) = shutil.disk_usage(p)
            total += total_
            used += used_
            free += free_

        # Only patch if its changed
        if state_total != total or state_used != used or state_free != free:
            disk_usage["total"] = total
            disk_usage["used"] = used
            disk_usage["free"] = free

            await patch_microscope(self.session, self.microscope_id, MicroscopeUpdate(state=state))


    async def on_event(self, event: FileSystemEvent):
        event_type = event.event_type

        # Code around issue with inode reuse
        if event_type == EVENT_TYPE_MOVED:
            event_type = EVENT_TYPE_CREATED
            event = FileCreatedEvent(event.dest_path)

        path = AsyncPath(event.src_path)

        # We are only looking for status files
        status_file_match = STATUS_PATTERN.match(path.name)
        if not (status_file_match and event_type in STATUS_FILE_EVENTS):
            return

        if event_type == EVENT_TYPE_DELETED:
            if await path.exists():
                return
            else:
                logger.info(f"Delete event for {path}")

        elif event_type in [EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED]:
            # The receivers are continually writing to their status files, we don't want to send
            # event if nothing has changes. So we stop sending events if nothing has changed for
            # 5 minutes. We store progress and last change time for each receiver to be able todo
            # this.
            receiver = status_file_match.group(1)

            try:
                status = ScanStatusFile.parse_file(path)
            except FileNotFoundError:
                return

            progress = status.progress

            update_receiver_progress = False
            if receiver in self._receiver_progress:
                (change_time, previous_progress) = self._receiver_progress[receiver]
                if f"{status.uuid}/{progress}" == previous_progress:
                    if change_time + timedelta(minutes=5) < datetime.utcnow():
                        # we can stop sending events, wait until something changes
                        return
                else:
                    update_receiver_progress = True
            else:
                update_receiver_progress = True

            if update_receiver_progress:
                self._receiver_progress[receiver] = (datetime.utcnow(), f"{status.uuid}/{progress}")

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

        await self._send_disk_usage(str(path))

    async def sync(self):
        files = await create_sync_snapshot(self.host, settings.WATCH_DIRECTORIES)
        async with aiohttp.ClientSession() as session:
            await post_sync_event(session, SyncEvent(files=files))
