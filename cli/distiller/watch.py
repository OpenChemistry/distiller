import asyncio
import logging
import platform
import sys
from datetime import datetime
from typing import List
import re

import aiohttp
import coloredlogs
import tenacity
from aiolimiter import AsyncLimiter
from aiopath import AsyncPath
from aiowatchdog import AIOEventHandler, AIOEventIterator
from config import settings
from constants import LOG_FILE_GLOB
from schemas import File
from schemas import FileSystemEvent as FileSystemEventModel
from schemas import SyncEvent
from watchdog.events import FileSystemEvent, EVENT_TYPE_CLOSED
from watchdog.observers import Observer

# Setup logger
logger = logging.getLogger("watch")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = coloredlogs.ColoredFormatter(
    "%(asctime)s,%(msecs)03d - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


async def create_sync_snapshot(watch_dirs: List[str]) -> List[File]:
    files = []
    host = platform.node()
    for watch_dir in watch_dirs:
        async for f in AsyncPath(watch_dir).glob(LOG_FILE_GLOB):
            path = AsyncPath(f)
            stat_info = await path.stat()
            created = datetime.fromtimestamp(stat_info.st_ctime)
            files.append(File(path=str(f), created=created, host=host))

    return files


async def watch(
    dirs: List[str], queue: asyncio.Queue, loop: asyncio.BaseEventLoop
) -> None:
    handler = AIOEventHandler(queue, loop)

    observer = Observer()
    for d in dirs:
        observer.schedule(handler, str(d))
    observer.start()

    files = await create_sync_snapshot(dirs)
    async with aiohttp.ClientSession() as session:
        await post_sync_event(session, SyncEvent(files=files))


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
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

        return await r.json()


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
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
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def upload_dm4(session: aiohttp.ClientSession, dm4_path: AsyncPath):
    data = aiohttp.FormData()
    headers = {
        settings.API_KEY_NAME: settings.API_KEY
    }
    async with dm4_path.open('rb') as fp:
        data.add_field('file', fp,
               filename=dm4_path.name,
               content_type='application/octet-stream')
        async with session.post(f"{settings.API_URL}/files/haadf", headers=headers, data=data) as r:
            r.raise_for_status()


async def monitor(queue: asyncio.Queue) -> None:
    #rate_limit = AsyncLimiter(100, 1)
    host = platform.node()

    log_pattern = re.compile(r"^log_scan([0-9]*)_.*\.data")
    dm4_pattern = re.compile(r"^scan([0-9]*)\.dm4")

    async with aiohttp.ClientSession() as session:
        while True:
            async for event in AIOEventIterator(queue):
                if isinstance(event, FileSystemEvent):
                    path = AsyncPath(event.src_path)

                    # We are only looking for log files and dm4s (haadf)
                    if not log_pattern.match(path.name) and not dm4_pattern.match(path.name):
                        continue

                    if  dm4_pattern.match(path.name) and event.event_type == EVENT_TYPE_CLOSED:
                        await upload_dm4(session, path)
                        continue

                    model = FileSystemEventModel(
                        event_type=event.event_type,
                        src_path=event.src_path,
                        is_directory=event.is_directory,
                        host=host,
                    )

                    if await path.exists():
                        stat_info = await path.stat()
                        model.created = datetime.fromtimestamp(stat_info.st_ctime)
                else:
                    model = event

     #           async with rate_limit:
                await post_file_event(session, model)
            await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()

    logger.info(f"Monitoring: {settings.WATCH_DIRECTORIES}")

    futures = [
        watch(settings.WATCH_DIRECTORIES, queue, loop),
        monitor(queue),
    ]

    loop.run_until_complete(asyncio.gather(*futures))
