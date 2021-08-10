from datetime import datetime
from typing import List

from pydantic import BaseModel


class Location(BaseModel):
    host: str
    path: str


class Scan(BaseModel):
    id: int
    scan_id: int
    log_files: int
    locations: List[Location]


class ScanCreate(BaseModel):
    scan_id: int
    created: datetime
    locations: List[Location]


class ScanUpdate(BaseModel):
    id: int
    log_files: int
    locations: List[Location]
