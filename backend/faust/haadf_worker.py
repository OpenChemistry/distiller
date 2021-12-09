import asyncio
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime

import aiohttp
import matplotlib.pyplot as plt
import ncempy.io as nio
import tenacity
from aiopath import AsyncPath

import faust
from config import settings
from constants import DATE_DIR_FORMAT, TOPIC_HAADF_FILE_EVENTS

# Setup logger
logger = logging.getLogger("haadf_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller", store="rocksdb://", broker=settings.KAFKA_URL, topic_partitions=1
)


class HaadfEvent(faust.Record):
    path: str
    scan_id: int


haadf_events_topic = app.topic(TOPIC_HAADF_FILE_EVENTS, value_type=HaadfEvent)


async def generate_haadf_image(tmp_dir: str, dm4_path: str, scan_id: int) -> AsyncPath:
    haadf = nio.read(dm4_path)
    img = haadf["data"]
    # TODO push to scan
    # haadf['pixelSize'] # this contains the real space pixel size (most important meta data)
    path = AsyncPath(tmp_dir) / f"{scan_id}.png"

    # Work around issue with how faust resets sys.stdout to an instance of FileLogProxy
    # which doesn't have the property buffer, which is check by Pillow when its writing
    # out the image, so just reset it to the real stdout while calling imsave.
    stdout = sys.stdout
    sys.stdout = sys.__stdout__
    plt.imsave(str(path), img)
    sys.stdout = stdout

    return path


async def copy_to_ncemhub(path: AsyncPath):

    stat_info = await path.stat()
    created_datetime = datetime.fromtimestamp(stat_info.st_ctime)

    date_dir = created_datetime.strftime(DATE_DIR_FORMAT)
    dest_path = AsyncPath(settings.HAADF_NCEMHUB_DM4_DATA_PATH) / date_dir / path.name
    await dest_path.parent.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, shutil.copy, path, dest_path)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    )
    | tenacity.retry_if_exception_type(aiohttp.client_exceptions.ClientResponseError)
    | tenacity.retry_if_exception_type(asyncio.exceptions.TimeoutError),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def upload_haadf_image(session: aiohttp.ClientSession, path: AsyncPath):
    # Now upload
    async with path.open("rb") as fp:
        headers = {settings.API_KEY_NAME: settings.API_KEY}
        data = aiohttp.FormData()
        data.add_field("file", fp, filename=path.name, content_type="image/png")

        return await session.post(
            f"{settings.API_URL}/files/haadf", headers=headers, data=data
        )


@app.agent(haadf_events_topic)
async def watch_for_haadf_events(haadf_events):

    async with aiohttp.ClientSession() as session:
        async for event in haadf_events:
            path = event.path
            scan_id = event.scan_id
            with tempfile.TemporaryDirectory() as tmp:
                await copy_to_ncemhub(AsyncPath(path))
                image_path = await generate_haadf_image(tmp, path, scan_id)
                r = await upload_haadf_image(session, image_path)
                r.raise_for_status()

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, os.remove, path)
