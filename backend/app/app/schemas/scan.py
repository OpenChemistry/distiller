from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel


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

    class Config:
        orm_mode = True


class ScanCreate(BaseModel):
    scan_id: int
    created: datetime
    locations: List[LocationCreate]


class ScanUpdate(BaseModel):
    log_files: int
    locations: List[LocationCreate]
