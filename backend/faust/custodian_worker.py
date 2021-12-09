import asyncio
import logging
from typing import List

import aiohttp
from fabric import Connection

import faust
from config import settings
from constants import COMPUTE_HOSTS, TOPIC_CUSTODIAN_EVENT
from utils import Scan

# Setup logger
logger = logging.getLogger("custodian_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller", store="rocksdb://", broker=settings.KAFKA_URL, topic_partitions=1
)


class RemoveScanFilesEvent(faust.Record):
    scan: Scan


custodian_events_topic = app.topic(
    TOPIC_CUSTODIAN_EVENT, value_type=RemoveScanFilesEvent
)


def remove(scan: Scan, host: str, paths: List[str]):
    result = Connection(f"{host}", user=f"{settings.CUSTODIAN_USER}").run(
        f"rm {scan.scan_id} {' '.join(paths)}", hide=True
    )
    if result.exited != 0:
        logger.error(
            "Error removing scan {scan.scan_id}({scan.id}), exit code: {result.exit_code}."
        )


@app.agent(custodian_events_topic)
async def watch_for_custodian_events(custodian_events):

    async with aiohttp.ClientSession() as session:
        async for event in custodian_events:
            scan = event.scan
            print(event)

            # Generate list of edge locations
            edge_locations = [l for l in scan.locations if l.host not in COMPUTE_HOSTS]
            edge_hosts = [l.host for l in edge_locations]
            assert len(set(edge_hosts)) == 1, "scan files on more than one edge host!"

            # List of paths to remove from
            paths = [l.path for l in edge_locations]
            edge_host = edge_locations[0].host

            print(paths)
            print(edge_host)

            logger.info(
                f"Remove scan files for {scan.scan_id}({scan.id}) from {edge_host}:{paths}."
            )

            def _log_exception(future: asyncio.Future) -> None:
                try:
                    future.result()
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("Exception removing files.")

            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, remove, scan, edge_host, paths)
            future.add_done_callback(_log_exception)
