import asyncio
import concurrent.futures
import logging
from typing import List

from fabric import Connection

import faust
from config import settings
from constants import TOPIC_CUSTODIAN_EVENTS
from faust_records import Scan

# Setup logger
logger = logging.getLogger("custodian_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller-custodain",
    store="rocksdb://",
    broker=settings.KAFKA_URL,
    topic_partitions=1,
)


class RemoveScanFilesEvent(faust.Record):
    scan: Scan
    host: str


custodian_events_topic = app.topic(
    TOPIC_CUSTODIAN_EVENTS, value_type=RemoveScanFilesEvent
)


def remove(scan: Scan, host: str, paths: List[str]):
    result = Connection(
        f"{host}",
        user=f"{settings.CUSTODIAN_USER}",
        connect_kwargs={"key_filename": settings.CUSTODIAN_PRIVATE_KEY},
    ).run(f"rm {scan.scan_id} {' '.join(paths)}", hide=True, pty=False)
    if result.exited != 0:
        logger.error(
            "Error removing scan {scan.scan_id}({scan.id}), exit code: {result.exit_code}."
        )


remove_thread_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=settings.CUSTODIAN_MAX_CONCURRENT_REMOVES
)


@app.agent(custodian_events_topic)
async def watch_for_custodian_events(custodian_events):
    async for event in custodian_events:
        scan = event.scan
        host = event.host

        if host not in settings.CUSTODIAN_VALID_HOSTS:
            logger.error(f"Invalid host: {host}")
            continue

        # List of paths to remove from
        paths = [l.path for l in scan.locations if l.host == host]

        if len(paths) == 0:
            logger.warn("No paths to remove.")
            continue

        logger.info(
            f"Remove scan files for {scan.scan_id}({scan.id}) from {host}:{paths}."
        )

        def _log_exception(future: asyncio.Future) -> None:
            try:
                future.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Exception removing files.")

        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(remove_thread_pool, remove, scan, host, paths)
        future.add_done_callback(_log_exception)
