from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.job import Job, JobState
from app.schemas.scan import Scan


# Has to go in separate module rather the job.py because of circular import.
class JobEventType(str, Enum):
    SUBMIT = "job.submit"
    UPDATED = "job.updated"
    CANCEL = "job.cancel"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class SubmitJobEvent(BaseModel):
    job: Job
    scan: Optional[Scan]
    event_type = JobEventType.SUBMIT


class RemoveScanFilesEvent(BaseModel):
    scan: Scan
    host: str


class UpdateJobEvent(BaseModel):
    id: int
    event_type: JobEventType
    slurm_id: Optional[int]
    state: Optional[JobState]
    output: Optional[str]
    elapsed: Optional[timedelta]
    submit: Optional[datetime]
    notes: Optional[str]
    scanIds: Optional[List[int]]
    event_type = JobEventType.UPDATED

    @classmethod
    def from_job(cls, job: Job):
        return cls(
            id=job.id,
            slurm_id=job.slurm_id,
            state=job.state,
            elapsed=job.elapsed,
            output=job.output,
            notes=job.notes,
            scanIds=job.scanIds,
            submit=job.submit,
        )


class CancelJobEvent(BaseModel):
    job: Job
    event_type = JobEventType.CANCEL
