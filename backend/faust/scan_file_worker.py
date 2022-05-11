import asyncio
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime
from typing import Any, Dict

import aiohttp
import matplotlib.pyplot as plt
import ncempy.io as nio
import tenacity
from aiopath import AsyncPath
from ncempy.io import dm

import faust
from config import settings
from constants import (DATE_DIR_FORMAT, TOPIC_HAADF_FILE_EVENTS,
                       TOPIC_SCAN_METADATA_EVENTS)
from faust_records import ScanMetadata

# Setup logger
logger = logging.getLogger("haadf_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller-haadf", store="rocksdb://", broker=settings.KAFKA_URL, topic_partitions=1
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
    created_datetime = datetime.fromtimestamp(stat_info.st_ctime).astimezone()

    date_dir = created_datetime.astimezone().strftime(DATE_DIR_FORMAT)
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


scan_metadata_events = app.topic(TOPIC_SCAN_METADATA_EVENTS, value_type=Dict[str, Any])


def extract_metadata(dm4_path: str):
    metadata = {}
    with dm.fileDM(dm4_path, on_memory=True) as dm_file:
        # Save most useful metadata

        # Only keep the most useful tags as meta data
        for key, value in dm_file.allTags.items():
            # Most useful starting tags
            image_tags_prefix = f"ImageList.{dm_file.numObjects}.ImageTags."
            image_data_prefix = f"ImageList.{dm_file.numObjects}.ImageData."
            image_tags_index = key.find(image_tags_prefix)
            image_data_index = key.find(image_data_prefix)
            if image_tags_index > -1:
                sub = key[image_tags_index + len(image_tags_prefix) :]
                metadata[sub] = value
            elif image_data_index > -1:
                sub = key[image_data_index + len(image_data_prefix) :]
                metadata[sub] = value

            # Remove unneeded keys
            remove_patterns = [
                "frame sequence",
                "Private",
                "Reference Images",
                "Frame.Intensity",
                "Area.Transform",
                "Parameters.Objects",
                "Device.Parameters",
            ]
            for key in list(metadata):
                for remove_pattern in remove_patterns:
                    if key.find(remove_pattern) > -1:
                        del metadata[key]

        # Store the X and Y pixel size, offset and unit
        try:
            metadata["PhysicalSizeX"] = metadata["Calibrations.Dimension.1.Scale"]
            metadata["PhysicalSizeXOrigin"] = metadata[
                "Calibrations.Dimension.1.Origin"
            ]
            metadata["PhysicalSizeXUnit"] = metadata["Calibrations.Dimension.1.Units"]
            metadata["PhysicalSizeY"] = metadata["Calibrations.Dimension.2.Scale"]
            metadata["PhysicalSizeYOrigin"] = metadata[
                "Calibrations.Dimension.2.Origin"
            ]
            metadata["PhysicalSizeYUnit"] = metadata["Calibrations.Dimension.2.Units"]
        except:
            metadata["PhysicalSizeX"] = 1
            metadata["PhysicalSizeXOrigin"] = 0
            metadata["PhysicalSizeXUnit"] = ""
            metadata["PhysicalSizeY"] = 1
            metadata["PhysicalSizeYOrigin"] = 0
            metadata["PhysicalSizeYUnit"] = ""

    return metadata


async def send_scan_metadata(scan_id: int, path: str):
    metadata = extract_metadata(path)
    scan_metadata = ScanMetadata(scan_id=scan_id, metadata=metadata)

    await scan_metadata_events.send(value=scan_metadata)


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

                await send_scan_metadata(scan_id, path)

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, os.remove, path)
