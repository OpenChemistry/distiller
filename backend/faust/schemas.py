from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dateutil.parser import parse
from pydantic import BaseModel, Field, field_validator

from json_utils import numpy_dumps


class Location(BaseModel):
    host: str
    path: str


class ScanStatusFile(BaseModel):
    time: datetime
    last_scan_number: int
    progress: float
    uuid: str = Field(None, alias="UUID")

    @field_validator("time", mode="before")
    @classmethod
    def time_validate(cls, v):
        return parse(v)


class Scan(BaseModel):
    id: int
    scan_id: Optional[int] = None
    progress: int
    locations: List[Location]
    created: datetime
    image_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    microscope_id: int
    uuid: Optional[str] = None


class ScanCreate(BaseModel):
    scan_id: int
    uuid: str
    created: datetime
    locations: List[Location]
    metadata: Optional[Dict[str, Any]] = None


class ScanUpdate(BaseModel):
    id: int
    progress: Optional[int] = None
    locations: Optional[List[Location]] = None
    metadata: Optional[Dict[str, Any]] = None

    def model_dump_json(self, *args, **kwargs):
        return numpy_dumps(self.model_dump(mode="python"), default=None)


class JobUpdate(BaseModel):
    id: int
    slurm_id: Optional[int] = None
    state: Optional[str] = None
    output: Optional[str] = None
    elapsed: Optional[timedelta] = None
    submit: Optional[datetime] = None
    notes: Optional[str] = None


class Job(BaseModel):
    id: int
    job_type: str
    scan_ids: Optional[List[int]] = None
    slurm_id: Optional[int] = None
    state: str
    machine: str
    submit: Optional[datetime] = None
    notes: Optional[str] = None


class SfapiJob(BaseModel):
    slurm_id: int
    name: str
    workdir: str
    state: str
    elapsed: timedelta
    submit: datetime


class Machine(BaseModel):
    name: str
    account: str
    qos: str
    qos_filter: Optional[str] = None
    nodes: int
    constraint: str
    ntasks: int
    ntasks_per_node: Optional[int] = None
    cpus_per_task: int
    cpu_bind: Optional[str] = None
    bbcp_dest_dir: str
    reservation: Optional[str] = None
    streaming_dest_dir: Optional[str] = None


class Microscope(BaseModel):
    id: int
    name: str
    config: Optional[Dict[str, Any]] = None
