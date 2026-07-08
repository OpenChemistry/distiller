from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, field_serializer

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
    scan: Optional[Scan] = None
    event_type: JobEventType = JobEventType.SUBMIT


class RemoveScanFilesEvent(BaseModel):
    scan: Scan
    host: str


class UpdateJobEvent(BaseModel):
    id: int
    slurm_id: Optional[int] = None
    state: Optional[JobState] = None
    output: Optional[str] = None
    elapsed: Optional[timedelta] = None
    submit: Optional[datetime] = None
    notes: Optional[str] = None
    scan_ids: Optional[List[int]] = None
    event_type: JobEventType = JobEventType.UPDATED

    @field_serializer("elapsed", when_used="json")
    def serialize_elapsed(self, elapsed: Optional[timedelta]) -> Optional[float]:
        return elapsed.total_seconds() if elapsed is not None else None


class CancelJobEvent(BaseModel):
    job: Job
    event_type: JobEventType = JobEventType.CANCEL
