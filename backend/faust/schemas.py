from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Location(BaseModel):
    host: str
    path: str


class Scan(BaseModel):
    id: int
    scan_id: int
    log_files: int
    locations: List[Location]
    haadf_path: Optional[str] = None


class ScanCreate(BaseModel):
    scan_id: int
    created: datetime
    locations: List[Location]


class ScanUpdate(BaseModel):
    id: int
    log_files: Optional[int]
    locations: Optional[List[Location]]


class JobUpdate(BaseModel):
    id: int
    slurm_id: Optional[int]
    state: Optional[str]
    output: Optional[str]


class Job(BaseModel):
    id: int
    job_type: str
    scan_id: int
    slurm_id: Optional[int]
    state: str


class SfapiJob(BaseModel):
    slurm_id: int
    name: str
    workdir: str
    state: str
