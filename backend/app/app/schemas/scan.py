from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.job import Job


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


class Scan(BaseModel):
    id: int
    scan_id: int
    log_files: int
    created: datetime
    locations: List[Location]
    haadf_path: Optional[str]
    notes: Optional[str]
    jobs: List[Job]
    metadata: Optional[Dict[str, Any]] = Field(alias="metadata_")
    microscope_id: int

    class Config:
        orm_mode = True


class ScanCreate(BaseModel):
    scan_id: int
    created: datetime
    locations: List[LocationCreate]
    metadata: Optional[Dict[str, Any]]
    microscope_id: Optional[int]


class ScanUpdate(BaseModel):
    log_files: Optional[int] = None
    locations: Optional[List[LocationCreate]] = None
    notes: Optional[str]
    haadf_path: Optional[str]
    metadata: Optional[Dict[str, Any]]


class ScanEventType(str, Enum):
    CREATED = "scan.created"
    UPDATED = "scan.updated"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class ScanEvent(BaseModel):
    id: int
    log_files: Optional[int]
    locations: Optional[List[Location]]
    event_type: ScanEventType


class ScanCreatedEvent(ScanEvent):
    scan_id: int
    created: datetime
    event_type = ScanEventType.CREATED
    haadf_path: Optional[str] = None


class ScanUpdateEvent(ScanEvent):
    event_type = ScanEventType.UPDATED
    jobs: Optional[List[Job]]
    haadf_path: Optional[str]
    notes: Optional[str]
