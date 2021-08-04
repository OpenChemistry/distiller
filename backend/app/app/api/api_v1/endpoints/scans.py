from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import (get_api_key, get_current_user, get_db,
                          oauth2_password_bearer_or_api_key)
from app.crud import scan as crud

router = APIRouter()


@router.post("", response_model=schemas.Scan)
def create_scan(
    scan: schemas.ScanCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_api_key),
):
    return crud.create_scan(db=db, scan=scan)


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
    db: Session = Depends(get_db),
):
    scans = crud.get_scans(
        db, skip=skip, limit=limit, scan_id=scan_id, state=state, created=created
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
)
def update_scan(
    id: int,
    payload: schemas.ScanUpdate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_api_key),
):

    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    return crud.update_scan(db, id, payload)


@router.delete("/{id}")
def update_scan(
    id: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)
):

    db_scan = crud.get_scan(db, id=id)
    if db_scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    return crud.delete_scan(db, id)
