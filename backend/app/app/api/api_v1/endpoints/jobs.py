from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_db, oauth2_password_bearer_or_api_key
from app.crud import job as crud
from app.crud import scan as scan_crud
from app.kafka.producer import (send_scan_event_to_kafka,
                                send_submit_job_event_to_kafka)
from app.schemas import SubmitJobEvent
from app.schemas.scan import ScanUpdateEvent

router = APIRouter()


@router.post(
    "",
    response_model=schemas.Job,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    scan = scan_crud.get_scan(db, job.scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    job = crud.create_job(db=db, job=job)

    scan = schemas.Scan.from_orm(scan)
    job = schemas.Job.from_orm(job)

    await send_submit_job_event_to_kafka(SubmitJobEvent(scan=scan, job=job))

    jobs = crud.get_jobs(db, scan_id=job.scan_id)
    await send_scan_event_to_kafka(ScanUpdateEvent(id=job.scan_id, jobs=jobs))

    return job


@router.get(
    "",
    response_model=List[schemas.Scan],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_jobs(
    skip: int = 0,
    limit: int = 100,
    scan_id: int = -1,
    db: Session = Depends(get_db),
):
    jobs = crud.get_jobs(db, skip=skip, limit=limit, scan_id=scan_id)

    return jobs


@router.get(
    "/{id}",
    response_model=schemas.Job,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_job(id: int, db: Session = Depends(get_db)):
    db_job = crud.get_job(db, id=id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return db_job


@router.patch(
    "/{id}",
    response_model=schemas.Job,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def update_job(
    id: int, payload: schemas.JobUpdate, db: Session = Depends(get_db)
):

    db_job = crud.get_job(db, id=id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    (updated, job) = crud.update_job(db, id, payload)

    if updated:
        jobs = crud.get_jobs(db, scan_id=job.scan_id)
        await send_scan_event_to_kafka(ScanUpdateEvent(id=job.scan_id, jobs=jobs))

    return job
