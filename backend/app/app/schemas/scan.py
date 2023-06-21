import math
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Location(BaseModel):
    id: int
    host: str
    path: str

    class Config:
        orm_mode = True


class LocationCreate(BaseModel):
    host: str
    path: str


class ScanState(str, Enum):
    TRANSFER = "transfer"
    COMPLETE = "complete"


# Need this validator so 'Infinity' stays as 'Infinity' rather than inf
# as postgres will not allow inf to be stored in JSON
def metadata_infinity(metadata):
    if metadata == math.inf:
        return "Infinity"
    elif isinstance(metadata, dict):
        for k, v in metadata.items():
            metadata[k] = metadata_infinity(v)

        return metadata
    elif isinstance(metadata, list):
        return [metadata_infinity(i) for i in metadata]

    return metadata


class Scan(BaseModel):
    id: int
    scan_id: Optional[int]
    progress: int
    created: datetime
    locations: List[Location]
    image_path: Optional[str]
    notes: Optional[str]
    jobIds: Optional[List[int]]
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata_")
    microscope_id: int
    uuid: Optional[str]

    _metadata_infinity = validator("metadata", allow_reuse=True)(metadata_infinity)

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj) -> "Scan":
        jobIds = [job.id for job in obj.jobs]
        locations = [Location.from_orm(location) for location in obj.locations]
        obj_dict = obj.__dict__.copy()
        obj_dict.pop("locations", None)
        return cls(**obj_dict, jobIds=jobIds, locations=locations)


class Scan4DCreate(BaseModel):
    scan_id: int
    created: datetime
    uuid: str
    locations: List[LocationCreate]
    metadata: Optional[Dict[str, Any]]
    microscope_id: Optional[int]

    _metadata_infinity = validator("metadata", allow_reuse=True)(metadata_infinity)


class ScanFromFileMetadata(BaseModel):
    created: datetime
    locations: List[LocationCreate]
    microscope_id: int


class ScanFromFile(BaseModel):
    sha: str
    created: datetime
    locations: List[LocationCreate]
    metadata: Optional[Dict[str, Any]]
    microscope_id: int

    _metadata_infinity = validator("metadata", allow_reuse=True)(metadata_infinity)


class ScanUpdate(BaseModel):
    progress: Optional[int] = None
    locations: Optional[List[LocationCreate]] = None
    notes: Optional[str]
    image_path: Optional[str]
    metadata: Optional[Dict[str, Any]]
    job_id: Optional[int]

    _metadata_infinity = validator("metadata", allow_reuse=True)(metadata_infinity)


class ScanEventType(str, Enum):
    CREATED = "scan.created"
    UPDATED = "scan.updated"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class ScanEvent(BaseModel):
    id: int
    progress: Optional[int]
    locations: Optional[List[Location]]
    event_type: ScanEventType


class ScanCreatedEvent(ScanEvent):
    microscope_id: int
    scan_id: Optional[int]
    created: datetime
    event_type = ScanEventType.CREATED
    image_path: Optional[str] = None


class ScanUpdateEvent(ScanEvent):
    event_type = ScanEventType.UPDATED
    jobIds: Optional[List[int]]
    image_path: Optional[str]
    notes: Optional[str]
