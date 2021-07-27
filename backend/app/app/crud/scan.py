from backend.app.app.schemas.scan import ScanState
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import constants


def get_scan(db: Session, id: int):
    return db.query(models.Scan).filter(models.Scan.id == id).first()


def get_scan_by_scan_id(db: Session, scan_id: int):
    return db.query(models.Scan).filter(models.Scan.scan_id == scan_id).first()


def get_scans(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    scan_id: int = -1,
    state: ScanState = None,
):
    query = db.query(models.Scan)
    if scan_id > -1:
        query = db.query.filter(models.Scan.scan_id == scan_id)

    if state is not None:
        if state == ScanState.TRANSFER:
            query = query.filter(models.Scan.log_files < constants.NUMBER_OF_LOG_FILES)
        elif state == ScanState.COMPLETE:

            query = query.filter(models.Scan.log_files == constants.NUMBER_OF_LOG_FILES)

    return query.offset(skip).limit(limit).all()


def create_scan(db: Session, scan: schemas.ScanCreate):
    db_scan = models.Scan(**scan.dict())
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)

    return db_scan


def update_scan(db: Session, id: int, updates: schemas.ScanUpdate):
    statement = (
        update(models.Scan)
        .where(models.Scan.id == id)
        .where(models.Scan.log_files < updates.log_files)
        .values(log_files=updates.log_files)
    )

    db.execute(statement)
    db.commit()

    return get_scan(db, id)


def delete_scan(db: Session, id: int) -> None:
    db.query(models.Scan).filter(models.Scan.id == id).delete()
    db.commit()
