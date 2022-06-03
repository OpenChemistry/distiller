import asyncio
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import aiohttp
import matplotlib.pyplot as plt
import ncempy.io as nio
import tenacity
from aiopath import AsyncPath
from ncempy.io import dm, emd, ser
from numpy import ndarray

import faust
from config import settings
from constants import (DATE_DIR_FORMAT, TOPIC_HAADF_FILE_EVENTS,
                       TOPIC_SCAN_FILE_EVENTS, TOPIC_SCAN_METADATA_EVENTS)
from faust_records import ScanMetadata
from utils import ScanUpdate, get_scan, update_scan

DATA_FILE_FORMATS = ["dm3", "dm4", "ser", "emd"]

# Setup logger
logger = logging.getLogger("haadf_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller-haadf", store="rocksdb://", broker=settings.KAFKA_URL, topic_partitions=1
)

# 4D Scan associated HAADF DM4
class HaadfEvent(faust.Record):
    path: str
    scan_id: int


# Scan file upload
class ScanFileUploadedEvent(faust.Record):
    id: int
    path: str


haadf_events_topic = app.topic(TOPIC_HAADF_FILE_EVENTS, value_type=HaadfEvent)


async def generate_image_from_data(
    tmp_dir: str, data_path: str, image_filename: str
) -> AsyncPath:
    file = nio.read(data_path)
    img = file["data"]
    # TODO push to scan
    # haadf['pixelSize'] # this contains the real space pixel size (most important meta data)
    path = AsyncPath(tmp_dir) / image_filename

    # Work around issue with how faust resets sys.stdout to an instance of FileLogProxy
    # which doesn't have the property buffer, which is check by Pillow when its writing
    # out the image, so just reset it to the real stdout while calling imsave.
    stdout = sys.stdout
    sys.stdout = sys.__stdout__
    plt.imsave(str(path), img)
    sys.stdout = stdout

    return path


async def generate_image(tmp_dir: str, path: str, image_filename: str) -> AsyncPath:
    ext = AsyncPath(path).suffix

    if ext not in [".dm4", ".dm3", ".ser", ".emd"]:
        raise Exception(f"Unsupported file format: {ext}")

    return await generate_image_from_data(tmp_dir, path, image_filename)


async def copy_to_ncemhub(src_path: AsyncPath, dest_path: AsyncPath):

    stat_info = await src_path.stat()
    created_datetime = datetime.fromtimestamp(stat_info.st_ctime).astimezone()

    date_dir = created_datetime.astimezone().strftime(DATE_DIR_FORMAT)
    dest_path = (
        AsyncPath(settings.HAADF_NCEMHUB_DM4_DATA_PATH) / date_dir / src_path.name
    )
    await dest_path.parent.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, shutil.copy, src_path, dest_path)


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


def clean_metadata(md):
    for k, v in md.items():
        if isinstance(v, dict):
            return clean_metadata(v)
        elif isinstance(v, bytes):
            md[k] = v.decode("utf8")
        elif isinstance(v, ndarray):
            md[k] = tuple(v)

    return md


def extract_dm_metadata(dm_path: str):
    metadata = {}
    with dm.fileDM(dm_path, on_memory=True) as dm_file:
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


def extract_ser_metadata(ser_path: str):
    with ser.fileSER(ser_path) as ser_file:
        # We just pull out the first image
        _, metadata = ser_file.getDataset(0)

        # Add header data for the ser file
        metadata.update(ser_file.head)

    # Clean up the data
    metadata = clean_metadata(metadata)

    # Store the X and Y pixel size, offset and unit
    try:
        metadata["Dimensions.1"] = metadata["ArrayShape"][0]
        metadata["Dimensions.2"] = metadata["ArrayShape"][1]
        metadata["PhysicalSizeX"] = metadata["Calibration"][0]["CalibrationDelta"]
        metadata["PhysicalSizeXOrigin"] = metadata["Calibration"][0][
            "CalibrationOffset"
        ]
        metadata["PhysicalSizeXUnit"] = "m"  # always meters
        metadata["PhysicalSizeY"] = metadata["Calibration"][1]["CalibrationDelta"]
        metadata["PhysicalSizeYOrigin"] = metadata["Calibration"][1][
            "CalibrationOffset"
        ]
        metadata["PhysicalSizeYUnit"] = "m"  # always meters
    except:
        logger.warning(f"Unable to extract PhysicalSize from: {ser_path}")

    return metadata


def extract_emi_metadata(emi_path: str):
    metadata = ser.read_emi(emi_path)
    metadata = clean_metadata(metadata)

    return metadata


def extract_emd_metadata(emd_path: str):
    metadata = {}

    # EMD Berkeley
    with emd.fileEMD(emd_path, readonly=True) as emd_file:
        # For now just grab the first dataset
        data_group = emd_file.list_emds[0]
        dataset = data_group["data"]

        try:
            name = data_group.name.split("/")[-1]
            metadata[name] = {}
            metadata[name].update(data_group.attrs)
        except:
            pass

        # Get the dim vectors
        dims = emd_file.get_emddims(data_group)
        if dataset.ndim == 2:
            dimY = dims[0]
            dimX = dims[1]
        elif dataset.ndim == 3:
            dimY = dims[1]
            dimX = dims[2]
        elif dataset.ndim == 4:
            dimY = dims[2]
            dimX = dims[3]
        else:
            dimY = None
            dimX = None

        if dimX is None or dimY is None:
            logger.warning("Unable to extract PhysicalSize, dims are not available")
        else:
            # Store the X and Y pixel size, offset and unit
            try:
                metadata["PhysicalSizeX"] = dimX[0][1] - dimX[0][0]
                metadata["PhysicalSizeXOrigin"] = dimX[0][0]
                metadata["PhysicalSizeXUnit"] = dimX[2].replace("_", "")
                metadata["PhysicalSizeY"] = dimY[0][1] - dimY[0][0]
                metadata["PhysicalSizeYOrigin"] = dimY[0][0]
                metadata["PhysicalSizeYUnit"] = dimY[2].replace("_", "")
            except:
                logger.warning(f"Unable to extract PhysicalSize from: {emd_path}")

        metadata["shape"] = dataset.shape

        metadata = clean_metadata(metadata)

    return metadata


def extract_metadata(path: str):
    ext = AsyncPath(path).suffix

    if ext in [".dm4", ".dm3"]:
        return extract_dm_metadata(path)
    elif ext in [".ser"]:
        return extract_ser_metadata(path)
    elif ext in [".emi"]:
        return extract_emi_metadata(path)
    elif ext == ".emd":
        return extract_emd_metadata(path)

    else:
        raise Exception(f"Unsupported file format: {ext}")


async def send_scan_metadata(session: aiohttp.ClientSession, scan_id: int, path: str):
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
                await copy_to_ncemhub(
                    AsyncPath(path), AsyncPath(settings.HAADF_NCEMHUB_DM4_DATA_PATH)
                )
                image_path = await generate_image(tmp, path, f"{scan_id}.png")
                r = await upload_haadf_image(session, image_path)
                r.raise_for_status()

                await send_scan_metadata(session, scan_id, path)

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, os.remove, path)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    )
    | tenacity.retry_if_exception_type(aiohttp.client_exceptions.ClientResponseError)
    | tenacity.retry_if_exception_type(asyncio.exceptions.TimeoutError),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def upload_image(session: aiohttp.ClientSession, id: int, path: AsyncPath):
    # Now upload
    async with path.open("rb") as fp:
        headers = {settings.API_KEY_NAME: settings.API_KEY}
        data = aiohttp.FormData()
        data.add_field("file", fp, filename=path.name, content_type="image/png")

        return await session.put(
            f"{settings.API_URL}/scans/{id}/image", headers=headers, data=data
        )


scan_file_events_topic = app.topic(
    TOPIC_SCAN_FILE_EVENTS, value_type=ScanFileUploadedEvent
)


@app.agent(scan_file_events_topic)
async def watch_for_scan_file_events(scan_file_events):

    async with aiohttp.ClientSession() as session:
        async for event in scan_file_events:
            path = event.path
            id = event.id
            with tempfile.TemporaryDirectory() as tmp:
                await copy_to_ncemhub(
                    AsyncPath(path), AsyncPath(settings.NCEMHUB_DATA_PATH)
                )

                if Path(path).suffix in DATA_FILE_FORMATS:
                    image_path = await generate_image(tmp, path, f"{id}.png")
                    r = await upload_image(session, id, image_path)
                    r.raise_for_status()

                # First get the current metadata to patch
                scan = await get_scan(session, id)
                metadata = scan.metadata
                if metadata is None:
                    metadata = {}
                metadata.update(extract_metadata(path))
                await update_scan(session, ScanUpdate(id=id, metadata=metadata))

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, os.remove, path)