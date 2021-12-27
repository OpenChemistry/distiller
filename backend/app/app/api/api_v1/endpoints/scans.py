import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security.api_key import APIKey
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_api_key, get_db, oauth2_password_bearer_or_api_key
from app.core.config import settings
from app.core.constants import COMPUTE_HOSTS
from app.crud import scan as crud
from app.kafka.producer import (send_remove_scan_files_event_to_kafka,
                                send_scan_event_to_kafka)
from app.models import Scan
from app.schemas.events import RemoveScanFilesEvent
from app.schemas.scan import ScanCreatedEvent
from app.core.logging import logger

router = APIRouter()


@router.post("", response_model=schemas.Scan)
async def create_scan(
    scan: schemas.ScanCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_api_key),
):

    scan = crud.create_scan(db=db, scan=scan)

    # See if we have HAADF image for this scan
    upload_path = Path(settings.HAADF_IMAGE_UPLOAD_DIR) / f"scan{scan.scan_id}.png"
    if upload_path.exists():
        # Move it to the right location to be served statically
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            shutil.move,
            upload_path,
            Path(settings.HAADF_IMAGE_STATIC_DIR) / f"{scan.id}.png",
        )

        # Finally update the haadf path
        (_, scan) = crud.update_scan(
            db, scan.id, haadf_path=f"{settings.HAADF_IMAGE_URL_PREFIX}/{scan.id}.png"
        )

    await send_scan_event_to_kafka(
        ScanCreatedEvent(**schemas.Scan.from_orm(scan).dict())
    )

    return scan


@router.get(
    "",
    response_model=List[schemas.Scan],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_scans(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    scan_id: int = -1,
    state: schemas.ScanState = None,
    created: datetime = None,
    has_haadf: bool = None,
    db: Session = Depends(get_db),
):
    scans = crud.get_scans(
        db,
        skip=skip,
        limit=limit,
        scan_id=scan_id,
        state=state,
        created=created,
        has_haadf=has_haadf,
    )

    count = crud.get_scans_count(
        db,
        skip=skip,
        limit=limit,
        scan_id=scan_id,
        state=state,
        created=created,
        has_haadf=has_haadf,
    )

    response.headers["X-Total-Count"] = str(count)

    return scans


@router.get(
    "/{id}",
    response_model=schemas.Scan,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_scan(id: int, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    return db_scan


@router.patch(
    "/{id}",
    response_model=schemas.Scan,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def update_scan(
    id: int, payload: schemas.ScanUpdate, db: Session = Depends(get_db)
):

    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    (updated, scan) = crud.update_scan(
        db,
        id,
        log_files=payload.log_files,
        locations=payload.locations,
        notes=payload.notes,
    )

    if updated:
        scan_updated_event = schemas.ScanUpdateEvent(id=id)
        if scan.log_files == payload.log_files:
            scan_updated_event.log_files = scan.log_files

        scan_updated_event.locations = [
            schemas.scan.Location.from_orm(l) for l in scan.locations
        ]

        if scan.notes is not None and scan.notes == payload.notes:
            scan_updated_event.notes = scan.notes

        await send_scan_event_to_kafka(scan_updated_event)

    return scan


async def _remove_scan_files(db_scan: Scan, host: str = None):
    if host is None:
        hosts = set([l.host for l in db_scan.locations if l.host not in COMPUTE_HOSTS])
    else:
        hosts = [host]

    for host in hosts:
        # Verify that we have scan files on this host
        locations = [l for l in db_scan.locations if l.host == host]
        if len(locations) == 0:
            raise HTTPException(status_code=400, detail="Invalid request")

        scan = schemas.Scan.from_orm(db_scan)
        await send_remove_scan_files_event_to_kafka(
            RemoveScanFilesEvent(scan=scan, host=host)
        )


@router.delete("/{id}", dependencies=[Depends(oauth2_password_bearer_or_api_key)])
async def delete_scan(id: int, remove_scan_files: bool, db: Session = Depends(get_db)):

    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    if remove_scan_files:
        logger.info("Removing scan files.")
        await _remove_scan_files(db_scan)

    crud.delete_scan(db, id)

    haadf_path = Path(settings.HAADF_IMAGE_STATIC_DIR) / f"{id}.png"
    logger.info(f"Checking if HAADF image exists: {haadf_path}")
    if haadf_path.exists():
        logger.info(f"Removing HAADF image: {haadf_path}")
        # Remove it
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.remove, haadf_path)


@router.put(
    "/{id}/remove",
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def remove_scan_files(id: int, host: str, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    await _remove_scan_files(db_scan, host)


@router.delete(
    "/{id}/locations/{location_id}",
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def delete_location(id: int, location_id: int, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    location = crud.get_location(db, id=location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    crud.delete_location(db, location_id)


@router.delete(
    "/{id}/locations",
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def remove_scan(id: int, host: str, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    crud.delete_locations(db, scan_id=id, host=host)

    db_scan = crud.get_scan(db, id=id)
    scan_updated_event = schemas.ScanUpdateEvent(id=id)
    if db_scan is not None:
        scan_updated_event.locations = db_scan.locations
        await send_scan_event_to_kafka(scan_updated_event)
