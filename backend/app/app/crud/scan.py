from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import desc, or_, update
from sqlalchemy.orm import Session

from app import models, schemas
from app.crud import job as job_crud
from app.crud import microscope


def get_scan(db: Session, id: int) -> models.Scan:
    return db.query(models.Scan).filter(models.Scan.id == id).first()


def get_scan_by_scan_id(db: Session, scan_id: int):
    return db.query(models.Scan).filter(models.Scan.scan_id == scan_id).first()


def _get_scans_query(
    db: Session,
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
    job_id: Optional[int] = None
):
    query = db.query(models.Scan)
    if scan_id > -1:
        query = query.filter(models.Scan.scan_id == scan_id)

    if state is not None:
        if state == schemas.ScanState.TRANSFER:
            query = query.filter(models.Scan.progress < 100)
        elif state == schemas.ScanState.COMPLETE:
            query = query.filter(models.Scan.progress == 100)

    if created is not None:
        query = query.filter(models.Scan.created == created)

    if has_image is not None:
        if has_image:
            query = query.filter(models.Scan.image_path != None)
        else:
            query = query.filter(models.Scan.image_path == None)

    if start is not None:
        query = query.filter(models.Scan.created > start)

    if end is not None:
        query = query.filter(models.Scan.created < end)

    if microscope_id is not None:
        query = query.filter(models.Scan.microscope_id == microscope_id)

    if sha is not None:
        query = query.filter(models.Scan.sha == sha)

    if uuid is not None:
        query = query.filter(models.Scan.uuid == uuid)

    if job_id is not None:
        query = query.filter(models.Scan.jobs.any(id=job_id))

    return query


def get_scans(
    db: Session,
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
    job_id: Optional[int] = None,
):
    query = _get_scans_query(
        db,
        skip,
        limit,
        scan_id,
        state,
        created,
        has_image,
        start,
        end,
        microscope_id,
        sha,
        uuid,
        job_id,
    )

    return query.order_by(desc(models.Scan.created)).offset(skip).limit(limit).all()


def get_scans_count(
    db: Session,
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
    job_id: Optional[int] = None,
):
    query = _get_scans_query(
        db,
        skip,
        limit,
        scan_id,
        state,
        created,
        has_image,
        start,
        end,
        microscope_id,
        sha,
        uuid,
        job_id,
    )

    return query.count()


def create_scan(
    db: Session,
    scan: Union[schemas.Scan4DCreate, schemas.ScanFromFile],
    image_path: Union[str, None] = None,
) -> models.Scan:
    locations = scan.locations
    scan.locations = []

    if scan.microscope_id is None:
        microscope_ids = [m.id for m in microscope.get_microscopes(db)]
        # We default to the first ( 4D Camera )
        scan.microscope_id = microscope_ids[0]

    # Note: We have to pass metadata as metadata_ as metadata is reserved!
    db_scan = models.Scan(**scan.dict(), image_path=image_path, metadata_=scan.metadata)
    db.add(db_scan)
    for l in locations:
        l = models.Location(**l.dict())
        db_scan.locations.append(l)
        db.add(l)
    db.commit()
    db.refresh(db_scan)

    return db_scan


def update_scan(
    db: Session,
    id: int,
    progress: Optional[int] = None,
    locations: Optional[List[schemas.LocationCreate]] = None,
    image_path: Optional[str] = None,
    notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    job_id: Optional[int] = None,
):
    updated = False

    if progress is not None:
        statement = (
            update(models.Scan)
            .where(models.Scan.id == id)
            .where(models.Scan.progress < progress)
            .values(progress=progress)
        )

        resultsproxy = db.execute(statement)
        progress_updated = resultsproxy.rowcount == 1
        updated = updated or progress_updated

    if locations is not None:
        locations_updated = False
        for l in locations:
            exists = (
                db.query(models.Location.id)
                .filter_by(scan_id=id, host=l.host, path=l.path)
                .first()
                is not None
            )
            if not exists:
                l = models.Location(**l.dict(), scan_id=id)
                db.add(l)
                locations_updated = True

        updated = updated or locations_updated

    if image_path is not None:
        statement = (
            update(models.Scan)
            .where(models.Scan.id == id)
            .where(
                or_(
                    models.Scan.image_path != image_path, models.Scan.image_path == None
                )
            )
            .values(image_path=image_path)
        )
        resultsproxy = db.execute(statement)
        image_path_updated = resultsproxy.rowcount == 1
        updated = updated or image_path_updated

    if notes is not None:
        statement = (
            update(models.Scan)
            .where(models.Scan.id == id)
            .where(or_(models.Scan.notes != notes, models.Scan.notes == None))
            .values(notes=notes)
        )
        resultsproxy = db.execute(statement)
        notes_updated = resultsproxy.rowcount == 1
        updated = updated or notes_updated

    if metadata is not None:
        statement = (
            update(models.Scan)
            .where(models.Scan.id == id)
            .where(
                or_(models.Scan.metadata_ != metadata, models.Scan.metadata_ == None)
            )
            .values(metadata_=metadata)
        )
        resultsproxy = db.execute(statement)
        metadata_updated = resultsproxy.rowcount == 1
        updated = updated or metadata_updated

    if job_id is not None:
        jobs_updated = False
        scan = get_scan(db, id)
        if scan is None:
            raise Exception(f"Scan with id {id} does not exist.")
        # If jobs get too large, this operation should be moved
        # to a db query and made optional
        if not any([job.id == job_id for job in scan.jobs]):
            job = job_crud.get_job(db, job_id)
            scan.jobs.append(job)
            jobs_updated = True

        updated = updated or jobs_updated

    db.commit()

    return (updated, get_scan(db, id))


def count(db: Session) -> int:
    return db.query(models.Scan).count()


def _delete_scan_jobs_by_types(db: Session, scan: models.Scan, types: List[schemas.JobType]) -> None:
    if scan:
        for job in scan.jobs:
            if job.job_type in types:
                db.query(models.Job).filter(models.Job.id == job.id).delete()


def delete_scan(db: Session, id: int) -> None:
    scan_query = db.query(models.Scan).filter(models.Scan.id == id)
    scan = scan_query.first()
    if scan:
        job_types_to_delete = [schemas.JobType.COUNT, schemas.JobType.TRANSFER]
        _delete_scan_jobs_by_types(db, scan, job_types_to_delete)
        scan_query.delete()
        db.commit()


def get_location(db: Session, id: int):
    return db.query(models.Location).filter(models.Location.id == id).first()


def delete_location(db: Session, id: int) -> None:
    db.query(models.Location).filter(models.Location.id == id).delete()
    db.commit()


def delete_locations(db: Session, scan_id: int, host: str) -> None:
    db.query(models.Location).filter(
        models.Location.scan_id == scan_id, models.Location.host == host
    ).delete()
    db.commit()


def get_prev_next_scan(
    db: Session, id: int
) -> Tuple[Union[int, None], Union[int, None]]:
    # Fetch the scan so we can constrain by microscope id
    scan = get_scan(db, id)

    if scan is None:
        raise Exception("Invalid scan id: {id}")

    prev_scan = (
        db.query(models.Scan.id)
        .order_by(models.Scan.id.desc())
        .filter(models.Scan.microscope_id == scan.microscope_id)
        .filter(models.Scan.id < id)
        .limit(1)
        .scalar()
    )
    next_scan = (
        db.query(models.Scan.id)
        .order_by(models.Scan.id.asc())
        .filter(models.Scan.microscope_id == scan.microscope_id)
        .filter(models.Scan.id > id)
        .limit(1)
        .scalar()
    )

    return (prev_scan, next_scan)
