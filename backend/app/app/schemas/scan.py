from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ScanState(str, Enum):
    TRANSFER = "transfer"
    COMPLETE = "complete"


class Scan(BaseModel):
    id: int
    scan_id: int
    log_files: int
    created: datetime

    class Config:
        orm_mode = True


class ScanCreate(BaseModel):
    scan_id: int
    created: datetime


class ScanUpdate(BaseModel):
    log_files: int
