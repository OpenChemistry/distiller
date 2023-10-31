import asyncio
import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast
from urllib.parse import unquote

import aiofiles
from fastapi import (APIRouter, Depends, File, HTTPException, Response,
                     UploadFile, status)
from fastapi.security.api_key import APIKey
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import schemas
from app.api.deps import get_api_key, get_db, oauth2_password_bearer_or_api_key
from app.api.utils import upload_to_file
from app.core.config import settings
from app.core.logging import logger
from app.crud import scan as crud
from app.kafka.producer import (send_remove_scan_files_event_to_kafka,
                                send_scan_event_to_kafka,
                                send_scan_file_event_to_kafka)
from app.models import Scan
from app.schemas.events import RemoveScanFilesEvent
from app.schemas.scan import Scan4DCreate, ScanCreatedEvent

router = APIRouter()


async def create_4d_scan(db: Session, scan: Scan4DCreate):
    scan = crud.create_scan(db=db, scan=scan)

    # See if we have HAADF image for this scan
    upload_path = Path(settings.IMAGE_UPLOAD_DIR) / f"scan{scan.scan_id}.png"
    if upload_path.exists():
        # Move it to the right location to be served statically
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            shutil.move,
            upload_path,
            Path(settings.IMAGE_STATIC_DIR) / f"{scan.id}.png",
        )

        # Finally update the haadf path
        (_, scan) = crud.update_scan(
            db,
            cast(int, scan.id),
            image_path=f"{settings.IMAGE_URL_PREFIX}/{scan.id}.png",
        )

    return scan


def generate_sha256(form_data: schemas.ScanFromFileMetadata):
    sha = hashlib.sha256()
    if len(form_data.locations) > 0:
        sha.update(form_data.locations[0].host.encode())
        sha.update(form_data.locations[0].path.encode())
    else:
        logger.warn(
            f"No location available for scan. Using only created time and microscopy."
        )

    sha.update(form_data.created.isoformat().encode())
    sha.update(str(form_data.microscope_id).encode())

    return sha.hexdigest()


async def create_scan_from_file(
    db,
    meta: schemas.ScanFromFileMetadata,
    file_upload: UploadFile,
    ser_file_upload: Optional[UploadFile],
):
    sha = generate_sha256(meta)

    # Check for existing scan with this sha
    if crud.get_scans_count(db, sha=sha) != 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Scan in SHA already exists"
        )

    scan_from_file = schemas.ScanFromFile(sha=sha, **meta.model_dump())

    scan = crud.create_scan(db=db, scan=scan_from_file)
    ext = Path(file_upload.filename).suffix
    upload_path = Path(settings.SCAN_FILE_UPLOAD_DIR) / f"{scan.id}{ext}"
    async with aiofiles.open(upload_path, "wb") as fp:
        await upload_to_file(file_upload, fp)

    # Send event so the metadata get extracted etc.
    await send_scan_file_event_to_kafka(
        schemas.ScanFileUploaded(
            path=str(upload_path), id=scan.id, filename=unquote(file_upload.filename)
        )
    )

    if ser_file_upload is not None:
        ext = Path(ser_file_upload.filename).suffix
        upload_path = Path(settings.SCAN_FILE_UPLOAD_DIR) / f"{scan.id}{ext}"
        async with aiofiles.open(upload_path, "wb") as fp:
            await upload_to_file(ser_file_upload, fp)

        # Send event so the metadata get extracted etc.
        await send_scan_file_event_to_kafka(
            schemas.ScanFileUploaded(
                path=str(upload_path),
                id=scan.id,
                filename=unquote(ser_file_upload.filename),
            )
        )

    return scan


# For this endpoint we are on our own! As we want to support two request types
# we have to the parsing ourself, the OpenAPI doc will not be correct!
@router.post(
    "",
    summary="Note: This API either take a JSON body for creating a 4D scan or a scan files. We are parsing the request manually, the OpenAPI documentation is not correct.",
    response_model=schemas.Scan,
    response_model_by_alias=False,
)
async def create_scan(
    request: Request,
    # Because we can only have "simple" form fields with a file upload
    # we encode the metadata in another str field.
    # file_metadata: Optional[schemas.ScanFromFileFormData] = Depends(to_file_meta),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_api_key),
):
    try:
        content_type = request.headers["content-type"]
        if content_type == "application/json":
            scan = schemas.Scan4DCreate.model_validate(await request.json())
            scan = await create_4d_scan(db, scan)
        elif content_type.startswith("multipart/form-data"):
            form_data = await request.form()

            file = form_data.get("file")
            if file is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request, scan file is required",
                )
            scan_metadata_str = form_data.get("scan_metadata")
            if scan_metadata_str is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request, scan metadata is required",
                )

            scan_metadata = schemas.ScanFromFileMetadata.model_validate_json(scan_metadata_str)

            # See if we have an associated ser file
            file_stem = Path(file.filename).stem.replace("%20", "\\ ")
            ser_file = form_data.get(f"{file_stem}.ser")
            scan = await create_scan_from_file(
                db, scan_metadata, file_upload=file, ser_file_upload=ser_file
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request type"
            )
    except ValidationError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request"
        )

    await send_scan_event_to_kafka(
        ScanCreatedEvent(**schemas.Scan.model_validate(scan).model_dump())
    )

    return scan


@router.get(
    "",
    response_model=List[schemas.Scan],
    response_model_by_alias=False,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_scans(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    scan_id: int = -1,
    state: Optional[schemas.ScanState] = None,
    created: Optional[datetime] = None,
    has_image: Optional[bool] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    microscope_id: Optional[int] = None,
    sha: Optional[str] = None,
    uuid: Optional[str] = None,
    db: Session = Depends(get_db),
):

    scans = crud.get_scans(
        db,
        skip=skip,
        limit=limit,
        scan_id=scan_id,
        state=state,
        created=created,
        has_image=has_image,
        start=start,
        end=end,
        microscope_id=microscope_id,
        sha=sha,
        uuid=uuid,
    )

    count = crud.get_scans_count(
        db,
        skip=skip,
        limit=limit,
        scan_id=scan_id,
        state=state,
        created=created,
        has_image=has_image,
        start=start,
        end=end,
        microscope_id=microscope_id,
        sha=sha,
        uuid=uuid,
    )

    response.headers["X-Total-Count"] = str(count)

    return scans


@router.get(
    "/{id}",
    response_model=schemas.Scan,
    response_model_by_alias=False,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_scan(response: Response, id: int, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    (prev_scan, next_scan) = crud.get_prev_next_scan(db, id)

    if prev_scan is not None:
        response.headers["X-Previous-Scan"] = str(prev_scan)

    if next_scan is not None:
        response.headers["X-Next-Scan"] = str(next_scan)

    return db_scan


@router.patch(
    "/{id}",
    response_model=schemas.Scan,
    response_model_by_alias=False,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def update_scan(
    id: int, payload: schemas.ScanUpdate, db: Session = Depends(get_db)
):

    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    (updated, scan) = crud.update_scan(
        db,
        id,
        progress=payload.progress,
        locations=payload.locations,
        notes=payload.notes,
        metadata=payload.metadata,
    )

    if updated:
        scan_updated_event = schemas.ScanUpdateEvent(id=id)
        if scan.progress == payload.progress:
            scan_updated_event.progress = cast(int, scan.progress)

        scan_updated_event.locations = [
            schemas.scan.Location.model_validate(l) for l in scan.locations
        ]

        if scan.notes is not None and scan.notes == payload.notes:
            scan_updated_event.notes = cast(str, scan.notes)

        await send_scan_event_to_kafka(scan_updated_event)

    return scan


async def _remove_scan_files(db_scan: Scan, host: Optional[str] = None):
    if host is None:
        comput_hosts = [m.name for m in settings.MACHINES]
        hosts = set([l.host for l in db_scan.locations if l.host not in comput_hosts])
    else:
        hosts = [host]

    for host in hosts:
        # Verify that we have scan files on this host
        locations = [l for l in db_scan.locations if l.host == host]
        if len(locations) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request"
            )

        scan = schemas.Scan.model_validate(db_scan)
        await send_remove_scan_files_event_to_kafka(
            RemoveScanFilesEvent(scan=scan, host=host)
        )


@router.delete("/{id}", dependencies=[Depends(oauth2_password_bearer_or_api_key)])
async def delete_scan(id: int, remove_scan_files: bool, db: Session = Depends(get_db)):

    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    if remove_scan_files:
        logger.info("Removing scan files.")
        await _remove_scan_files(db_scan)

    crud.delete_scan(db, id)

    image_path = Path(settings.IMAGE_STATIC_DIR) / f"{id}.png"
    logger.info(f"Checking if image exists: {image_path}")
    if image_path.exists():
        logger.info(f"Removing image: {image_path}")
        # Remove it
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.remove, image_path)


@router.put(
    "/{id}/remove",
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def remove_scan_files(id: int, host: str, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    await _remove_scan_files(db_scan, host)


@router.delete(
    "/{id}/locations/{location_id}",
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def delete_location(id: int, location_id: int, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    location = crud.get_location(db, id=location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )

    crud.delete_location(db, location_id)


@router.delete(
    "/{id}/locations",
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def remove_scan(id: int, host: str, db: Session = Depends(get_db)):
    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )

    crud.delete_locations(db, scan_id=id, host=host)

    db_scan = crud.get_scan(db, id=id)
    scan_updated_event = schemas.ScanUpdateEvent(id=id)
    if db_scan is not None:
        scan_updated_event.locations = db_scan.locations
        await send_scan_event_to_kafka(scan_updated_event)


@router.put("/{id}/image")
async def upload_image(
    id: int,
    file: UploadFile = File(...),
    api_key: APIKey = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> None:
    upload_path = Path(settings.IMAGE_STATIC_DIR) / f"{id}.png"
    async with aiofiles.open(upload_path, "wb") as fp:
        await upload_to_file(file, fp)

    image_path = f"{settings.IMAGE_URL_PREFIX}/{id}.png"
    (updated, _) = crud.update_scan(db, id, image_path=str(image_path))
    if updated:
        await send_scan_event_to_kafka(
            schemas.ScanUpdateEvent(image_path=image_path, id=id)
        )
