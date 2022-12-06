import asyncio
import logging
import platform
import re
import signal
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import List
import platform

import aiohttp

import coloredlogs
import tenacity
from aiopath import AsyncPath
from pathlib import Path
from aiowatchdog import AIOEventHandler, AIOEventIterator
from cachetools import TTLCache
from config import settings
from schemas import File, WatchMode
from schemas import FileSystemEvent as FileSystemEventModel
from schemas import SyncEvent, Microscope
from watchdog.events import (EVENT_TYPE_MODIFIED, EVENT_TYPE_CREATED)

if settings.POLL or settings.MODE in [WatchMode.SCAN_4D_FILES, WatchMode.SCAN_4D_HAADF_FILES]:
    from watchdog.observers.polling import PollingObserver as Observer
else:
    from watchdog.observers import Observer

from utils import logger, get_microscope
from modes import ModeHandler


def get_host():
    if settings.HOST is None:
        host = platform.node()
    else:
        host = settings.HOST

    return host


async def watch(host: str,
    microscope_id: int, dirs: List[str], queue: asyncio.Queue, loop: asyncio.BaseEventLoop
) -> None:
    handler = AIOEventHandler(queue, loop)

    observer = Observer()
    for d in dirs:
        observer.schedule(handler, str(d), recursive=settings.RECURSIVE)
    observer.start()

    if settings.SYNC:
        mode = settings.MODE
        async with aiohttp.ClientSession() as session:
            handler = get_mode_handler(mode, session, microscope_id, host)
            logger.info("Running sync.")
            await handler.sync()


def get_mode_handler(mode: WatchMode, session: aiohttp.ClientSession, microscope_id: int, host: str) -> ModeHandler:
    if mode == WatchMode.SCAN_4D_FILES:
        from modes.scan_4d_files import Scan4DFilesModeHandler
        return Scan4DFilesModeHandler(microscope_id, host, session)
    elif mode == WatchMode.SCAN_4D_HAADF_FILES:
        from modes.scan_4d_haadf_files import Scan4DHAADFFilesModeHandler
        return Scan4DHAADFFilesModeHandler(microscope_id, host, session)
    elif mode == WatchMode.SCAN_FILES:
        from modes.scan_files import ScanFilesModeHandler
        return ScanFilesModeHandler(microscope_id, host, session)
    else:
        raise Exception(f"Unrecognized mode: {mode}")


async def monitor(microscope_id: int, queue: asyncio.Queue) -> None:
    host = get_host()

    cache = TTLCache(maxsize=100000, ttl=30)

    try:
        async with aiohttp.ClientSession() as session:
            # Select handler based on mode
            mode = settings.MODE
            handler = get_mode_handler(mode, session, microscope_id, host)
            while True:
                async for event in AIOEventIterator(queue):
                    await handler.on_event(event)


    except asyncio.CancelledError:
        logger.info("Monitor loop canceled.")
    except Exception:
        logger.exception("Exception in monitoring loop.")

async def get_microscope_id(name: str) -> int:
    async with aiohttp.ClientSession() as session:
        microscope = await get_microscope(session, name)

        return microscope.id

async def shutdown(signal, loop, monitor_task):
    logger.info(f"Received exit signal {signal.name}...")
    logger.info(f"Canceling monitoring task.")
    monitor_task.cancel()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    logger.info(f"Waiting for {len(tasks)} to complete.")
    await asyncio.gather(*tasks)
    logger.info(f"Stopping event loop.")
    loop = asyncio.get_event_loop()
    loop.stop()

def main():
    loop = asyncio.get_event_loop()

    queue = asyncio.Queue()

    logger.info(f"Monitoring: {settings.WATCH_DIRECTORIES}")
    logger.info(f"Watch mode: {settings.MODE}")
    logger.info(f"Using: {Observer.__name__}")
    logger.info(f"Microscopy: {settings.MICROSCOPE}")
    microscope_id = asyncio.run(get_microscope_id(settings.MICROSCOPE))

    loop.create_task(watch(get_host(), microscope_id, settings.WATCH_DIRECTORIES, queue, loop))
    monitor_task = loop.create_task(monitor(microscope_id, queue))

    # Install signal handler ( not in Windows )
    if platform.system() != "Windows":
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(shutdown(s, loop, monitor_task))
            )

    loop.run_forever()

if __name__ == "__main__":
    main()