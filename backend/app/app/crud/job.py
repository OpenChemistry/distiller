from datetime import datetime
from typing import Optional, Tuple, Union, cast

from sqlalchemy import desc, or_, update
from sqlalchemy.orm import Session

from app import models, schemas
from app.crud import scan as scan_crud


def get_job(db: Session, id: int):
    return db.query(models.Job).filter(models.Job.id == id).first()


def get_job_by_slurm_id(db: Session, slurm_id: int):
    return db.query(models.Job).filter(models.Job.slurm_id == slurm_id).first()


def _get_jobs_query(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    slurm_id: Optional[int] = None,
    job_type: Optional[schemas.JobType] = None,
    scan_id: Optional[int] = None
):
    query = db.query(models.Job)

    if slurm_id is not None:
        query = query.filter(models.Job.slurm_id == slurm_id)

    if job_type is not None:
        query = query.filter(models.Job.job_type == job_type)

    if start is not None:
        query = query.filter(models.Job.submit > start)

    if end is not None:
        query = query.filter(models.Job.submit < end)

    if scan_id is not None:
        query = query.filter(models.Job.scans.any(id=scan_id))

    return query


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    slurm_id: Optional[int] = None,
    job_type: Optional[schemas.JobType] = None,
    scan_id: Optional[int] = None
):
    query = _get_jobs_query(db, skip, limit, start, end, slurm_id, job_type, scan_id)

    return query.order_by(desc(models.Job.id)).offset(skip).limit(limit).all()


def get_jobs_count(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    slurm_id: Optional[int] = None,
    job_type: Optional[schemas.JobType] = None,
    scan_id: Optional[int] = None
):
    query = _get_jobs_query(db, skip, limit, start, end, slurm_id, job_type, scan_id)

    return query.count()


def create_job(db: Session, job: schemas.JobCreate):
    _job = job.dict()
    scan_id = _job.pop("scan_id")
    db_job = models.Job(**_job)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    if scan_id is not None:
        add_scan_to_job(db, cast(int, db_job.id), scan_id)
        db.commit()
        db.refresh(db_job)

    return db_job

def add_scan_to_job(db: Session, id: int, scan_id: int) -> bool:
    scans_updated = False
    scan = scan_crud.get_scan(db, scan_id)

    if scan is None:
        raise Exception(f"Scan with id {scan_id} does not exist.")
    
    job = get_job(db, id)

    if job is not None and not any([s.id == scan_id for s in job.scans]):
        job.scans.append(scan)
        scans_updated = True

    return scans_updated


def update_job(
    db: Session, id: int, updates: schemas.JobUpdate
) -> Tuple[bool, models.Job]:
    statement = update(models.Job).where(models.Job.id == id)

    or_comparisons = []
    updated = False

    if updates.state is not None:
        statement = statement.values(state=updates.state)
        or_comparisons.append(models.Job.state != updates.state)

    if updates.slurm_id is not None:
        statement = statement.values(slurm_id=updates.slurm_id)
        or_comparisons.append(models.Job.slurm_id != updates.slurm_id)
        or_comparisons.append(models.Job.slurm_id == None)

    if updates.output is not None:
        statement = statement.values(output=updates.output)
        or_comparisons.append(models.Job.output != updates.output)
        or_comparisons.append(models.Job.output == None)

    if updates.elapsed is not None:
        statement = statement.values(elapsed=updates.elapsed)
        or_comparisons.append(models.Job.elapsed != updates.elapsed)
        or_comparisons.append(models.Job.elapsed == None)

    if updates.submit is not None:
        statement = statement.values(submit=updates.submit)
        or_comparisons.append(models.Job.submit != updates.submit)
        or_comparisons.append(models.Job.submit == None)

    if updates.notes is not None:
        statement = statement.values(notes=updates.notes)
        or_comparisons.append(models.Job.notes != updates.notes)
        or_comparisons.append(models.Job.notes == None)

    if updates.scan_id is not None:
        scans_updated = add_scan_to_job(db, id, updates.scan_id)
        updated = updated or scans_updated

    if or_comparisons:
        statement = statement.where(or_(*or_comparisons))

        resultproxy = db.execute(statement)
        updated = resultproxy.rowcount == 1 or updated

    db.commit()

    return (updated, get_job(db, id))


def get_prev_next_job(
    db: Session, id: int
) -> Tuple[Union[int, None], Union[int, None]]:
    job = get_job(db, id)

    if job is None:
        raise Exception("Invalid job id: {id}")

    prev_job = (
        db.query(models.Job.id)
        .order_by(models.Job.id.desc())
        .filter(models.Job.job_type == job.job_type)
        .filter(models.Job.id < id)
        .limit(1)
        .scalar()
    )
    next_job = (
        db.query(models.Job.id)
        .order_by(models.Job.id.asc())
        .filter(models.Job.job_type == job.job_type)
        .filter(models.Job.id > id)
        .limit(1)
        .scalar()
    )

    return (prev_job, next_job)
