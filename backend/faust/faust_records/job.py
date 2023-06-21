from enum import Enum
from typing import Dict, List, Optional, Union

import faust
from .scan import Scan


class JobType(str, Enum):
    COUNT = "count"
    TRANSFER = "transfer"
    STREAMING = "streaming"

    def __str__(self) -> str:
        return self.value


class Job(faust.Record):
    id: int
    job_type: JobType
    machine: str
    params: Dict[str, Union[str, int, float]]
    scanIds: Optional[List[int]]


class JobEventType(str, Enum):
    SUBMIT = "job.submit"
    CANCEL = "job.cancel"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class JobEvent(faust.Record):
    job: Job
    event_type: JobEventType


class SubmitJobEvent(JobEvent):
    scan: Optional[Scan]
    event_type: JobEventType = JobEventType.SUBMIT
