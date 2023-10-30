from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dateutil.parser import parse
from pydantic import field_validator, ConfigDict, BaseModel, Field

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
    created: str
    locations: List[Location]
    metadata: Optional[Dict[str, Any]] = None


class ScanUpdate(BaseModel):
    id: int
    progress: Optional[int] = None
    locations: Optional[List[Location]] = None
    metadata: Optional[Dict[str, Any]] = None
    # TODO[pydantic]: The following keys were removed: `json_dumps`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(json_dumps=numpy_dumps)


class JobUpdate(BaseModel):
    id: int
    slurm_id: Optional[int] = None
    state: Optional[str] = None
    output: Optional[str] = None
    elapsed: Optional[timedelta] = None


class Job(BaseModel):
    id: int
    job_type: str
    scan_id: int
    slurm_id: Optional[int] = None
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
    qos_filter: Optional[str] = None
    nodes: int
    constraint: str
    ntasks: int
    ntasks_per_node: Optional[int] = None
    cpus_per_task: int
    cpu_bind: Optional[str] = None
    bbcp_dest_dir: str
    reservation: Optional[str] = None


class Microscope(BaseModel):
    id: int
    name: str
    config: Optional[Dict[str, Any]] = None
