import asyncio
import re
import shutil
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security.api_key import APIKey
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.core.config import settings
from app.crud import scan as scan_crud
from app.kafka.producer import (send_filesystem_event_to_kafka,
                                send_haadf_event_to_kafka,
                                send_scan_event_to_kafka,
                                send_sync_event_to_kafka)

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
    await send_sync_event_to_kafka(event)

    return event


async def upload_haadf_dm4(file: UploadFile) -> None:
    scan_regex = re.compile(r"^scan([0-9]*)\.dm4")

    # Extract out the scan ids
    match = scan_regex.match(file.filename)
    if not match:
        raise HTTPException(status_code=400, detail="Can't extract scan id.")

    scan_id = match.group(1)
    upload_path = Path(settings.HAADF_DM4_UPLOAD_DIR) / f"scan{scan_id}.dm4"
    async with aiofiles.open(upload_path, "wb") as fp:
        contents = await file.read()
        await fp.write(contents)

    await send_haadf_event_to_kafka(
        schemas.HaadfUploaded(path=str(upload_path), scan_id=scan_id)
    )


async def upload_haadf_png(db: Session, file: UploadFile) -> None:
    scan_regex = re.compile(r"^([0-9]*)\.png")

    # Extract out the scan ids
    match = scan_regex.match(file.filename)
    if not match:
        raise HTTPException(status_code=400, detail="Can't extract scan id.")

    scan_id = int(match.group(1))
    upload_path = Path(settings.HAADF_IMAGE_UPLOAD_DIR) / f"scan{scan_id}.png"
    async with aiofiles.open(upload_path, "wb") as fp:
        contents = await file.read()
        await fp.write(contents)

    scans = scan_crud.get_scans(db, scan_id=scan_id, has_haadf=False)

    if len(scans) > 1:
        raise Exception("More than one scan exists without HAADF!")
    elif len(scans) == 1:
        scan = scans[0]
        # Move the file to the right location
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            shutil.move,
            upload_path,
            Path(settings.HAADF_IMAGE_STATIC_DIR) / f"{scan.id}.png",
        )

        (updated, _) = scan_crud.update_scan(
            db, scan.id, haadf_path=f"{settings.HAADF_IMAGE_URL_PREFIX}/{scan.id}.png"
        )

        if updated:
            await send_scan_event_to_kafka(
                schemas.ScanUpdate(haadf_path=str(upload_path), id=scan.id)
            )


@router.post("/haadf")
async def upload_haadf(
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    api_key: APIKey = Depends(deps.get_api_key),
) -> None:
    suffix = Path(file.filename).suffix

    if suffix.lower() == ".dm4":
        await upload_haadf_dm4(file)
    elif suffix.lower() == ".png":
        await upload_haadf_png(db, file)
    else:
        raise HTTPException(status_code=400, detail="Invalid format.")
