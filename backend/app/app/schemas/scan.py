import math
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, BaseModel, Field, validator

from app.schemas.job import Job


class Location(BaseModel):
    id: int
    host: str
    path: str
    model_config = ConfigDict(from_attributes=True)


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
    scan_id: Optional[int] = None
    progress: int
    created: datetime
    locations: List[Location]
    image_path: Optional[str] = None
    notes: Optional[str] = None
    jobs: List[Job]
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_")
    microscope_id: int
    uuid: Optional[str] = None

    _metadata_infinity = validator("metadata", allow_reuse=True)(metadata_infinity)
    model_config = ConfigDict(from_attributes=True)


class Scan4DCreate(BaseModel):
    scan_id: int
    created: datetime
    uuid: str
    locations: List[LocationCreate]
    metadata: Optional[Dict[str, Any]] = None
    microscope_id: Optional[int] = None

    _metadata_infinity = validator("metadata", allow_reuse=True)(metadata_infinity)


class ScanFromFileMetadata(BaseModel):
    created: datetime
    locations: List[LocationCreate]
    microscope_id: int


class ScanFromFile(BaseModel):
    sha: str
    created: datetime
    locations: List[LocationCreate]
    metadata: Optional[Dict[str, Any]] = None
    microscope_id: int

    _metadata_infinity = validator("metadata", allow_reuse=True)(metadata_infinity)


class ScanUpdate(BaseModel):
    progress: Optional[int] = None
    locations: Optional[List[LocationCreate]] = None
    notes: Optional[str] = None
    image_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

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
    progress: Optional[int] = None
    locations: Optional[List[Location]] = None
    event_type: ScanEventType


class ScanCreatedEvent(ScanEvent):
    microscope_id: int
    scan_id: Optional[int] = None
    created: datetime
    event_type = ScanEventType.CREATED
    image_path: Optional[str] = None


class ScanUpdateEvent(ScanEvent):
    event_type = ScanEventType.UPDATED
    jobs: Optional[List[Job]] = None
    image_path: Optional[str] = None
    notes: Optional[str] = None
