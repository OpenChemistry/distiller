import asyncio
import logging
import sys
from datetime import datetime
from typing import List

import aiohttp
import coloredlogs
import tenacity
from aiopath import AsyncPath
from aiowatchdog import AIOEventHandler, AIOEventIterator
from config import settings
from constants import LOG_FILE_GLOB
from schemas import FileSystemEvent as FileSystemEventModel
from watchdog.events import FileClosedEvent, FileCreatedEvent
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


async def dispatch_existing_logs(watch_dir: str, evh: AIOEventHandler):
    loop = asyncio.get_event_loop()
    async for f in AsyncPath(watch_dir).glob(LOG_FILE_GLOB):
        event = FileCreatedEvent(str(f))
        await loop.run_in_executor(None, evh.dispatch, event)
        event = FileClosedEvent(str(f))
        await loop.run_in_executor(None, evh.dispatch, event)


async def watch(
    dirs: List[str], queue: asyncio.Queue, loop: asyncio.BaseEventLoop
) -> None:
    handler = AIOEventHandler(queue, loop)

    observer = Observer()
    for d in dirs:
        observer.schedule(handler, str(d))
    observer.start()

    for d in dirs:
        await dispatch_existing_logs(d, handler)

    loop.call_soon_threadsafe(queue.put_nowait, None)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def post_event(
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


async def monitor(queue: asyncio.Queue) -> None:
    semaphore = asyncio.Semaphore(1)

    async with aiohttp.ClientSession() as session:
        while True:
            async for event in AIOEventIterator(queue):
                path = AsyncPath(event.src_path)

                model = FileSystemEventModel(
                    event_type=event.event_type,
                    src_path=event.src_path,
                    is_directory=event.is_directory,
                )

                if await path.exists():
                    stat_info = await path.stat()
                    model.created = datetime.fromtimestamp(stat_info.st_ctime)

                async with semaphore:
                    await post_event(session, model)
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
