from datetime import datetime

from pydantic import BaseModel


class Scan(BaseModel):
    id: int
    scan_id: int
    log_files: int


class ScanCreate(BaseModel):
    scan_id: int
    created: datetime


class ScanUpdate(BaseModel):
    id: int
    log_files: int
