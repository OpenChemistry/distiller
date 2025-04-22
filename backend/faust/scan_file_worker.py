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
from constants import (DATE_DIR_FORMAT, NERSC_LOCATION,
                       TOPIC_HAADF_FILE_EVENTS, TOPIC_SCAN_FILE_EVENTS,
                       TOPIC_SCAN_METADATA_EVENTS)
from faust_records import ScanMetadata
from schemas import Location
from utils import ScanUpdate, generate_ncemhub_scan_path, get_scan, update_scan

DATA_FILE_FORMATS = [".dm3", ".dm4", ".ser", ".emd"]

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
    # The original filename provided by the user
    filename: str


haadf_events_topic = app.topic(TOPIC_HAADF_FILE_EVENTS, value_type=HaadfEvent)


async def generate_image_from_data(
    tmp_dir: str, data_path: str, image_filename: str
) -> AsyncPath:
    # Hack to get around problem with memory mapping in spin!
    if Path(data_path).suffix in [".dm3", ".dm4"]:
        file = dm.dmReader(data_path, on_memory=False)
    else:
        file = nio.read(data_path)

    img = file["data"]

    # If we have more than 2 dimensions just pick the first image
    if img.ndim > 2:
        slc = [0] * (img.ndim - 2)
        img = img[tuple(slc)]

    path = AsyncPath(tmp_dir) / image_filename

    format = settings.IMAGE_FORMAT
    pil_kwargs = {}

    if settings.IMAGE_QUALITY is not None:
        pil_kwargs["quality"] = settings.IMAGE_QUALITY

    # Work around issue with how faust resets sys.stdout to an instance of FileLogProxy
    # which doesn't have the property buffer, which is check by Pillow when its writing
    # out the image, so just reset it to the real stdout while calling imsave.
    stdout = sys.stdout
    sys.stdout = sys.__stdout__
    plt.imsave(str(path), img, format=format, pil_kwargs=pil_kwargs)
    sys.stdout = stdout

    return path


async def generate_image(tmp_dir: str, path: str, image_filename: str) -> AsyncPath:
    ext = AsyncPath(path).suffix

    if ext not in [".dm4", ".dm3", ".ser", ".emd"]:
        raise Exception(f"Unsupported file format: {ext}")

    return await generate_image_from_data(tmp_dir, path, image_filename)


async def ensure_date_directory(src_path: AsyncPath, dest_path: AsyncPath):
    stat_info = await src_path.stat()
    created_datetime = datetime.fromtimestamp(stat_info.st_ctime).astimezone()

    date_dir = created_datetime.astimezone().strftime(DATE_DIR_FORMAT)
    dest_path = dest_path / date_dir

    await dest_path.mkdir(parents=True, exist_ok=True)

    return dest_path


async def copy_to_ncemhub(src_path: AsyncPath, dest_path: AsyncPath):
    loop = asyncio.get_event_loop()
    await dest_path.parent.mkdir(parents=True, exist_ok=True)
    await loop.run_in_executor(None, shutil.copy, src_path, dest_path)


async def copy_file_to_ncemhub(src_path: AsyncPath, dest_path: AsyncPath):
    dest_path = await ensure_date_directory(src_path, dest_path)

    await copy_to_ncemhub(src_path, dest_path / src_path.name)


async def generate_ncemhub_scan_file_path(
    session: aiohttp.ClientSession, src_path: AsyncPath, id: int, filename: str
):
    stat_info = await src_path.stat()
    created_datetime = datetime.fromtimestamp(stat_info.st_ctime).astimezone()

    created_date = created_datetime.astimezone().strftime(DATE_DIR_FORMAT)

    return (
        await generate_ncemhub_scan_path(
            session, settings.NCEMHUB_DATA_PATH, created_date, id
        )
        / filename
    )


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    )
    | tenacity.retry_if_exception_type(aiohttp.client_exceptions.ClientResponseError)
    | tenacity.retry_if_exception_type(asyncio.exceptions.TimeoutError),
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def upload_haadf_image(session: aiohttp.ClientSession, path: AsyncPath):
    format = settings.IMAGE_FORMAT
    # Now upload
    async with path.open("rb") as fp:
        headers = {settings.API_KEY_NAME: settings.API_KEY}
        data = aiohttp.FormData()
        data.add_field("file", fp, filename=path.name, content_type=f"image/{format}")

        return await session.post(
            f"{settings.API_URL}/files/haadf", headers=headers, data=data
        )


scan_metadata_events = app.topic(TOPIC_SCAN_METADATA_EVENTS, value_type=Dict[str, Any])


def clean_metadata(md):
    for k, v in md.items():
        if isinstance(v, dict):
            clean_metadata(v)
        elif isinstance(v, bytes):
            md[k] = v.decode("utf8")
        elif isinstance(v, ndarray):
            md[k] = tuple(v)

    return md


def extract_dm_metadata(dm_path: str):
    metadata = {}

    GOOD_KEYS = [
        "Calibrations",
        "Acquisition",
        "DataBar",
        "EELS",
        "Meta Data",
        "Microscope Info",
        "Session Info",
        "4Dcamera",
        "DigiScan",
        "Dimensions",
    ]

    # Use on_memory=False for now as it doesn't seem to work on spin
    with dm.fileDM(dm_path, on_memory=False) as dm_file:
        # Save most useful metadata
        for tag_key, tag_value in dm_file.allTags.items():
            if any(x in tag_key for x in GOOD_KEYS):
                tag_key_split = tag_key.split(".")
                if "DigiScan" in tag_key:
                    if "Rotation" in tag_key:
                        new_key = " ".join(tag_key_split[4:])
                        metadata[new_key] = tag_value
                elif "Session Info" in tag_key:
                    if "Label" in tag_key_split[-1]:
                        label = tag_value
                        value_key_split = tag_key_split.copy()
                        value_key_split[-1] = "Value"
                        value_key = ".".join(value_key_split)
                        if value_key in dm_file.allTags:
                            metadata[label] = dm_file.allTags[value_key]
                else:
                    new_key = " ".join(tag_key_split[4:])
                    metadata[new_key] = tag_value

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


def extract_ncem_emd_metadata(emd_file):
    metadata = {}

    try:
        metadata["user"] = {}
        metadata["user"].update(emd_file.file_hdl["/user"].attrs)
    except:
        pass
    try:
        metadata["microscope"] = {}
        metadata["microscope"].update(emd_file.file_hdl["/microscope"].attrs)
    except:
        pass
    try:
        metadata["sample"] = {}
        metadata["sample"].update(emd_file.file_hdl["/sample"].attrs)
    except:
        pass
    try:
        metadata["comments"] = {}
        metadata["comments"].update(emd_file.file_hdl["/comments"].attrs)
    except:
        pass
    try:
        metadata["stage"] = {}
        # Check for legacy keys in stage group. Skip the rest
        good_keys = ("position", "type", "Type")
        for k in good_keys:
            if k in emd_file.file_hdl["/stage"].attrs:
                metadata["stage"][k] = emd_file.file_hdl["/stage"].attrs[k]
    except:
        pass

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
            dimZ = None
            dimY = dims[0]
            dimX = dims[1]
        elif dataset.ndim == 3:
            dimZ = dims[0]
            dimY = dims[1]
            dimX = dims[2]
        elif dataset.ndim == 4:
            dimZ = dims[1]
            dimY = dims[2]
            dimX = dims[3]
        else:
            dimZ = None
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
                metadata["Dimensions.1"] = dimX[0].shape[0]
                metadata["Dimensions.2"] = dimY[0].shape[0]
                if dimZ is not None:
                    metadata["PhysicalSizeZ"] = dimZ[0][1] - dimZ[0][0]
                    metadata["PhysicalSizeZOrigin"] = dimZ[0][0]
                    metadata["PhysicalSizeZUnit"] = dimZ[2]

            except:
                logger.warning(f"Unable to extract PhysicalSize from: {emd_path}")

        metadata["shape"] = dataset.shape
        metadata.update(extract_ncem_emd_metadata(emd_file))
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
    format = settings.IMAGE_FORMAT
    async with aiohttp.ClientSession() as session:
        async for event in haadf_events:
            path = event.path
            scan_id = event.scan_id
            with tempfile.TemporaryDirectory() as tmp:
                await copy_file_to_ncemhub(
                    AsyncPath(path), AsyncPath(settings.HAADF_NCEMHUB_DM4_DATA_PATH)
                )
                image_path = await generate_image(tmp, path, f"{scan_id}.{format}")
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def upload_image(session: aiohttp.ClientSession, id: int, path: AsyncPath):
    format = settings.IMAGE_FORMAT
    # Now upload
    async with path.open("rb") as fp:
        headers = {settings.API_KEY_NAME: settings.API_KEY}
        data = aiohttp.FormData()
        data.add_field("file", fp, filename=path.name, content_type=f"image/{format}")

        return await session.put(
            f"{settings.API_URL}/scans/{id}/image", headers=headers, data=data
        )


scan_file_events_topic = app.topic(
    TOPIC_SCAN_FILE_EVENTS, value_type=ScanFileUploadedEvent
)


@app.agent(scan_file_events_topic)
async def watch_for_scan_file_events(scan_file_events):
    format = settings.IMAGE_FORMAT
    async with aiohttp.ClientSession() as session:
        async for event in scan_file_events:
            path = event.path
            id = event.id
            with tempfile.TemporaryDirectory() as tmp:
                try:
                    try:
                        ncemhub_path = await generate_ncemhub_scan_file_path(
                            session, AsyncPath(path), id, event.filename
                        )
                        await copy_to_ncemhub(AsyncPath(path), ncemhub_path)
                    except Exception:
                        logger.exception("Exception copying to ncemhub.")
                        raise

                    if Path(path).suffix in DATA_FILE_FORMATS:
                        try:
                            image_path = await generate_image(
                                tmp, path, f"{id}.{format}"
                            )
                        except Exception:
                            logger.exception("Exception generating image.")
                            raise

                        try:
                            r = await upload_image(session, id, image_path)
                            r.raise_for_status()
                        except Exception:
                            logger.exception("Exception uploading image.")
                            raise

                    # First get the current metadata to patch
                    try:
                        scan = await get_scan(session, id)
                        metadata = scan.metadata
                        if metadata is None:
                            metadata = {}
                        metadata.update(extract_metadata(path))

                        # Patch the locations to include the location at NERSC
                        locations = scan.locations
                        locations.append(
                            Location(host=NERSC_LOCATION, path=str(ncemhub_path))
                        )

                        await update_scan(
                            session,
                            ScanUpdate(id=id, metadata=metadata, locations=locations),
                        )
                    except Exception:
                        logger.exception("Exception extracting metadata.")
                        raise
                except Exception:
                    logger.exception(f"Exception processing scan file: {path}.")
                finally:
                    if Path(path).exists():
                        loop = asyncio.get_event_loop()
                        loop.run_in_executor(None, os.remove, path)
