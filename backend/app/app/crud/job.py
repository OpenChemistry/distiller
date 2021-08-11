from typing import Tuple

from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app import models, schemas


def get_job(db: Session, id: int):
    return db.query(models.Job).filter(models.Job.id == id).first()


def get_job_by_slurm_id(db: Session, slurm_id: int):
    return db.query(models.Job).filter(models.Job.slurm_id == slurm_id).first()


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    scan_id: int = None,
    slurm_id: int = None,
):
    query = db.query(models.Job)
    if scan_id is not None:
        query = query.filter(models.Job.scan_id == scan_id)

    if slurm_id is not None:
        query = query.filter(models.Job.slurm_id == slurm_id)

    return query.offset(skip).limit(limit).all()


def create_job(db: Session, job: schemas.JobCreate):
    db_job = models.Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job


def update_job(
    db: Session, id: int, updates: schemas.JobUpdate
) -> Tuple[bool, models.Job]:
    statement = update(models.Job).where(models.Job.id == id)

    or_comparisons = []

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

    statement = statement.where(or_(*or_comparisons))

    resultproxy = db.execute(statement)
    updated = resultproxy.rowcount == 1
    db.commit()

    return (updated, get_job(db, id))
