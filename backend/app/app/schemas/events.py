from pydantic import BaseModel

from app.schemas.job import Job
from app.schemas.scan import Scan


# Has to go in separate module rather the job.py because of circular import.
class SubmitJobEvent(BaseModel):
    job: Job
    scan: Scan


class RemoveScanFilesEvent(BaseModel):
    scan: Scan
    host: str
