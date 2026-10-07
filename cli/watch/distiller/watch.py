import asyncio
import logging
import platform
import re
import signal
import sys
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from signal import Signals
from typing import List, Optional

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

if settings.POLL or settings.MODE in [
    WatchMode.SCAN_4D_FILES,
    WatchMode.SCAN_4D_HAADF_FILES,
    WatchMode.ARINA_SCAN_FILES,
]:
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


async def watch(
    host: str,
    microscope_id: int,
    dirs: List[str],
    queue: asyncio.Queue,
    loop: asyncio.BaseEventLoop,
    observer: Observer,
) -> None:
    handler = AIOEventHandler(queue, loop)

    for d in dirs:
        observer.schedule(handler, str(d), recursive=settings.RECURSIVE)
    observer.daemon = True
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
    elif mode == WatchMode.ARINA_SCAN_FILES:
        from modes.arina_scan_files import ArinaScanFilesModeHandler
        return ArinaScanFilesModeHandler(microscope_id, host, session)
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
                    try:
                        await handler.on_event(event)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception("Error processing event: %s", str(event))

    except asyncio.CancelledError:
        logger.info("Monitor loop canceled.")


async def get_microscope_id(name: str) -> int:
    async with aiohttp.ClientSession() as session:
        microscope = await get_microscope(session, name)

        return microscope.id

def _stop_observer_sync(observer: Observer) -> None:
    try:
        observer.stop()
        observer.join(timeout=5.0)
    except Exception:
        logger.exception("Error stopping observer.")


async def _stop_observer(
    observer: Observer,
    loop: asyncio.AbstractEventLoop,
    timeout: float = 5.0,
) -> None:
    if observer is None or not observer.is_alive():
        return
    logger.info("Stopping observer.")
    done_event = asyncio.Event()

    def _worker():
        try:
            _stop_observer_sync(observer)
        finally:
            if not loop.is_closed():
                loop.call_soon_threadsafe(done_event.set)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    try:
        await asyncio.wait_for(done_event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Observer cleanup timed out.")


async def shutdown(
    loop: asyncio.AbstractEventLoop,
    signal=None,
    observer: Optional[Observer] = None,
) -> None:
    if signal is not None:
        try:
            signal_name = Signals(signal).name
        except Exception:
            signal_name = getattr(signal, "name", str(signal))
        logger.info(f"Received exit signal {signal_name}...")

    if observer is not None and observer.is_alive():
        await _stop_observer(observer, loop, timeout=5.0)

    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    if tasks:
        logger.info(f"Waiting for {len(tasks)} tasks to complete.")
        for t in tasks:
            t.cancel()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                logger.error("Error during task cancellation: %s", res)

    logger.info("Stopping event loop.")
    loop.stop()


async def _windows_wakeup() -> None:
    while True:
        await asyncio.sleep(0.5)


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    queue = asyncio.Queue()

    logger.info(f"Monitoring: {settings.WATCH_DIRECTORIES}")
    logger.info(f"Watch mode: {settings.MODE}")
    logger.info(f"Using: {Observer.__name__}")
    logger.info(f"Microscopy: {settings.MICROSCOPE}")

    observer: Optional[Observer] = None
    _shutdown_task: Optional[asyncio.Task] = None
    startup_error: Optional[BaseException] = None

    def _trigger_shutdown(signal=None) -> asyncio.Task:
        nonlocal _shutdown_task
        if _shutdown_task is None:
            _shutdown_task = loop.create_task(
                shutdown(loop, signal, observer)
            )
        return _shutdown_task

    # Install signal handlers and Windows wakeup task BEFORE startup
    if platform.system() == "Windows":
        # On Windows, asyncio event loop blocks in GetQueuedCompletionStatus
        # with INFINITE timeout when idle, which prevents the main thread
        # from processing Ctrl-C (SIGINT). A periodic wakeup task ensures
        # signals are processed promptly.
        loop.create_task(_windows_wakeup())

        def _windows_signal_handler(signal, frame):
            if loop.is_running():
                loop.call_soon_threadsafe(_trigger_shutdown, signal)

        signals_to_handle = [signal.SIGINT, signal.SIGTERM]
        if hasattr(signal, "SIGBREAK"):
            signals_to_handle.append(signal.SIGBREAK)

        for s in signals_to_handle:
            try:
                signal.signal(s, _windows_signal_handler)
            except (ValueError, AttributeError):
                pass
    else:
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(s, _trigger_shutdown, s)

    async def _start():
        nonlocal observer, startup_error
        try:
            microscope_id = await get_microscope_id(settings.MICROSCOPE)
            observer = Observer()
            watch_task = loop.create_task(
                watch(get_host(), microscope_id, settings.WATCH_DIRECTORIES, queue, loop, observer)
            )
            loop.create_task(monitor(microscope_id, queue))
            await watch_task
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception as exc:
            startup_error = exc
            logger.exception("Failed to start watch service.")
            _trigger_shutdown(None)

    loop.create_task(_start())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt...")
        task = _trigger_shutdown(signal.SIGINT)
        if not task.done():
            loop.run_until_complete(task)
    finally:
        if not loop.is_closed():
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                logger.exception("Error shutting down async generators.")
            loop.close()

    if startup_error is not None:
        raise startup_error


if __name__ == "__main__":
    main()