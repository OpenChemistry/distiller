from datetime import datetime

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
    state: schemas.ScanState = None,
    created: datetime = None,
):
    query = db.query(models.Scan)
    if scan_id > -1:
        query = query.filter(models.Scan.scan_id == scan_id)

    if state is not None:
        if state == schemas.ScanState.TRANSFER:
            query = query.filter(models.Scan.log_files < constants.NUMBER_OF_LOG_FILES)
        elif state == schemas.ScanState.COMPLETE:

            query = query.filter(models.Scan.log_files == constants.NUMBER_OF_LOG_FILES)

    if created is not None:
        query = query.filter(models.Scan.created == created)

    return query.offset(skip).limit(limit).all()


def create_scan(db: Session, scan: schemas.ScanCreate):
    locations = scan.locations
    scan.locations = []
    db_scan = models.Scan(**scan.dict())
    db.add(db_scan)
    for l in locations:
        l = models.Location(**l.dict())
        db_scan.locations.append(l)
        db.add(l)
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
    locations = updates.locations
    for l in locations:
        exists = db.query(models.Location.id).filter_by(scan_id=id, host=l.host, path=l.path).first() is not None
        if not exists:
            l = models.Location(**l.dict(), scan_id=id)
            db.add(l)

    db.execute(statement)
    db.commit()

    return get_scan(db, id)


def delete_scan(db: Session, id: int) -> None:
    db.query(models.Scan).filter(models.Scan.id == id).delete()
    db.commit()


def get_location(db: Session, id: int):
    return db.query(models.Location).filter(models.Location.id == id).first()

def delete_location(db: Session, id: int) -> None:
    db.query(models.Location).filter(models.Location.id == id).delete()
    db.commit()
