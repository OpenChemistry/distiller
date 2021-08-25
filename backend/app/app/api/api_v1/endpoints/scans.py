import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import (get_api_key, get_current_user, get_db,
                          oauth2_password_bearer_or_api_key)
from app.core.config import settings
from app.crud import scan as crud
from app.kafka.producer import send_scan_event_to_kafka
from app.schemas.scan import ScanCreatedEvent

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

    return scans


@router.get("/{id}", response_model=schemas.Scan)
def read_scan(
    id: int, db: Session = Depends(get_db), _: schemas.User = Depends(get_current_user)
):
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


@router.delete("/{id}")
async def delete_scan(
    id: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)
):

    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

        # See if we have HAADF image for this scan
    upload_path = Path(settings.HAADF_IMAGE_UPLOAD_DIR) / f"scan{scan.scan_id}.png"

    crud.delete_scan(db, id)

    haadf_path = Path(settings.HAADF_IMAGE_STATIC_DIR) / f"{id}.png"
    if upload_path.exists():
        # Remove it
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.remove, haadf_path)


@router.delete("/{id}/locations/{location_id}")
def delete_location(
    id: int,
    location_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_api_key),
):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    location = crud.get_location(db, id=location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    return crud.delete_location(db, location_id)
