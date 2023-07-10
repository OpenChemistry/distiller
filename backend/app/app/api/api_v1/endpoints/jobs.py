from datetime import datetime
from typing import List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_db, oauth2_password_bearer_or_api_key
from app.crud import job as crud
from app.crud import scan as scan_crud
from app.kafka.producer import send_job_event_to_kafka, send_scan_event_to_kafka
from app.schemas import CancelJobEvent, SubmitJobEvent, UpdateJobEvent

router = APIRouter()


@router.post(
    "",
    response_model=schemas.Job,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def create_job(job_create: schemas.JobCreate, db: Session = Depends(get_db)):
    job = crud.create_job(db=db, job=job_create)

    if job is None:
        raise HTTPException(status_code=500, detail="Job creation failed.")
    
    scan = job.scans[0] if job.scans else None

    await send_job_event_to_kafka(SubmitJobEvent(job=schemas.Job.from_orm(job), scan=scan))

    return job


@router.get(
    "",
    response_model=List[schemas.Job],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_jobs(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    job_type: Optional[schemas.JobType] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
    scan_id: Optional[int] = None
):
    db_jobs = crud.get_jobs(
        db, skip=skip, limit=limit, job_type=job_type, start=start, end=end, scan_id=scan_id
    )
    count = crud.get_jobs_count(
        db, skip=skip, limit=limit, job_type=job_type, start=start, end=end, scan_id=scan_id
    )
    response.headers["X-Total-Count"] = str(count)

    return [schemas.Job.from_orm(job) for job in db_jobs]


@router.get(
    "/{id}",
    response_model=schemas.Job,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_job(response: Response, id: int, db: Session = Depends(get_db)):
    db_job = crud.get_job(db, id=id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    (prev_job, next_job) = crud.get_prev_next_job(db, id)

    if prev_job is not None:
        response.headers["X-Previous-Job"] = str(prev_job)

    if next_job is not None:
        response.headers["X-Next-Job"] = str(next_job)

    return schemas.Job.from_orm(db_job)


@router.get(
    "/{id}/scans",
    response_model=List[schemas.Scan],
    response_model_by_alias=False,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_job_scans(id: int, db: Session = Depends(get_db)):
    db_job = crud.get_job(db, id=id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    scans = db_job.scans
    return [schemas.Scan.from_orm(scan) for scan in scans]


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
    job = schemas.Job.from_orm(job)
    if updated:
        job_updated_event = UpdateJobEvent(**job.dict())

        if payload.scan_id:
            scan_updated_event = schemas.ScanUpdateEvent(id=payload.scan_id)
            db_scan = scan_crud.get_scan(db, id=payload.scan_id)
            scan_updated_event.job_ids = schemas.Scan.from_orm(db_scan).job_ids
            await send_scan_event_to_kafka(scan_updated_event)

        await send_job_event_to_kafka(job_updated_event)

    return job


@router.delete(
    "/{id}",
    response_model=schemas.Job,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def cancel_job(id: int, db: Session = Depends(get_db)):
    db_job = crud.get_job(db, id=id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    job = schemas.Job.from_orm(db_job)
    await send_job_event_to_kafka(CancelJobEvent(job=job))

    return job
