import asyncio
import datetime
import re
import shutil
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security.api_key import APIKey
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.api.utils import upload_to_file
from app.core.config import settings
from app.core.logging import logger
from app.crud import scan as scan_crud
from app.kafka.producer import (send_filesystem_event_to_kafka,
                                send_haadf_event_to_kafka,
                                send_log_file_sync_event_to_kafka,
                                send_scan_event_to_kafka,
                                send_scan_file_sync_event_to_kafka)

router = APIRouter()


@router.post("")
async def file_events(
    event: schemas.FileSystemEvent, api_key: APIKey = Depends(deps.get_api_key)
):
    await send_filesystem_event_to_kafka(event)

    return event


@router.post("/sync")
async def sync_events(
    event: schemas.SyncEvent, api_key: APIKey = Depends(deps.get_api_key)
):
    # The 4D camera doesn't see an id ( for now! )
    if event.microscope_id is None:
        await send_log_file_sync_event_to_kafka(event)
    else:
        await send_scan_file_sync_event_to_kafka(event)

    return event


async def upload_haadf_dm4(file: UploadFile) -> None:
    scan_regex = re.compile(r"^scan([0-9]*)\.dm4")

    # Extract out the scan ids
    match = scan_regex.match(file.filename)
    if not match:
        raise HTTPException(status_code=400, detail="Can't extract scan id.")

    scan_id = match.group(1)
    upload_path = Path(settings.SCAN_FILE_UPLOAD_DIR) / f"scan{scan_id}.dm4"
    async with aiofiles.open(upload_path, "wb") as fp:
        await upload_to_file(file, fp)

    await send_haadf_event_to_kafka(
        schemas.HaadfUploaded(path=str(upload_path), scan_id=scan_id)
    )


async def upload_haadf_image(db: Session, file: UploadFile) -> None:
    format = settings.IMAGE_FORMAT
    scan_regex = re.compile(f"^([0-9]*)\.{format}")

    # Extract out the scan ids
    match = scan_regex.match(file.filename)
    if not match:
        raise HTTPException(status_code=400, detail="Can't extract scan id.")

    scan_id = int(match.group(1))
    upload_path = Path(settings.IMAGE_UPLOAD_DIR) / f"scan{scan_id}.{format}"
    async with aiofiles.open(upload_path, "wb") as fp:
        await upload_to_file(file, fp)

    current_time = datetime.datetime.utcnow()
    created_since = current_time - datetime.timedelta(
        hours=settings.HAADF_SCAN_AGE_LIMIT
    )

    scans = scan_crud.get_scans(
        db, scan_id=scan_id, has_image=False, start=created_since
    )

    if len(scans) > 0:
        scan = scans[0]
        logger.info(f"Adding HAADF image '{upload_path}' to scan {scan.id}")
        # Move the file to the right location
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            shutil.move,
            upload_path,
            Path(settings.IMAGE_STATIC_DIR) / f"{scan.id}.{format}",
        )

        image_path = f"{settings.IMAGE_URL_PREFIX}/{scan.id}.{format}"
        (updated, _) = scan_crud.update_scan(db, scan.id, image_path=image_path)

        if updated:
            await send_scan_event_to_kafka(
                schemas.ScanUpdateEvent(image_path=image_path, id=scan.id)
            )


@router.post("/haadf")
async def upload_haadf(
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    api_key: APIKey = Depends(deps.get_api_key),
) -> None:
    suffix = Path(file.filename).suffix
    format = settings.IMAGE_FORMAT
    if suffix.lower() == ".dm4":
        await upload_haadf_dm4(file)
    elif suffix.lower() == f".{format}":
        await upload_haadf_image(db, file)
    else:
        raise HTTPException(status_code=400, detail="Invalid format.")
