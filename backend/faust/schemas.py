from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from json_utils import numpy_dumps


class Location(BaseModel):
    host: str
    path: str


class Scan(BaseModel):
    id: int
    scan_id: Optional[int]
    log_files: int
    locations: List[Location]
    created: datetime
    image_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]]


class ScanCreate(BaseModel):
    scan_id: int
    created: datetime
    locations: List[Location]
    metadata: Optional[Dict[str, Any]]


class ScanUpdate(BaseModel):
    id: int
    log_files: Optional[int]
    locations: Optional[List[Location]]
    metadata: Optional[Dict[str, Any]]

    class Config:
        json_dumps = numpy_dumps


class JobUpdate(BaseModel):
    id: int
    slurm_id: Optional[int]
    state: Optional[str]
    output: Optional[str]
    elapsed: Optional[timedelta]


class Job(BaseModel):
    id: int
    job_type: str
    scan_id: int
    slurm_id: Optional[int]
    state: str
    machine: str


class SfapiJob(BaseModel):
    slurm_id: int
    name: str
    workdir: str
    state: str
    elapsed: timedelta


class Machine(BaseModel):
    name: str
    account: str
    qos: str
    qos_filter: Optional[str]
    nodes: int
    constraint: str
    ntasks: int
    ntasks_per_node: Optional[int]
    cpus_per_task: int
    cpu_bind: Optional[str]
    bbcp_dest_dir: str
    reservation: Optional[str]


class Microscope(BaseModel):
    id: int
    name: str
    config: Optional[Dict[str, Any]]
