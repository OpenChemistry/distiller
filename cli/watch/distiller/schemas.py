from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


class WatchMode(str, Enum):
    # Watch for 4D scan logs
    SCAN_4D_FILES = "scan_4d_files"
    # Watch for DM4 files containing HAADF associated with a 4D scan
    SCAN_4D_HAADF_FILES = "scan_4d_haadf_files"
    # Watch for scan files to create scans from
    SCAN_FILES  = "scan_files"


class FileSystemEventType(str, Enum):
    MOVED = "moved"
    DELETED = "deleted"
    CREATED = "created"
    MODIFIED = "modified"
    CLOSED = "closed"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class FileSystemEvent(BaseModel):
    event_type: FileSystemEventType
    host: str
    src_path: str
    is_directory: bool
    created: Optional[datetime] = None
    content: Optional[str] = None


class File(BaseModel):
    host: str
    path: str
    created: Optional[datetime] = None
    content: Optional[str] = None


class SyncEvent(BaseModel):
    microscope_id: Optional[int]
    files: List[File]

class Location(BaseModel):
    host: str
    path: str

class ScanFromFileMetadata(BaseModel):
    created: datetime
    locations: List[Location]
    microscope_id: int

class Microscope(BaseModel):
    id: int
    name: str
    config: Optional[Dict[str, Any]]
    state: Optional[Dict[str, Any]]

class Scan(BaseModel):
    id: int
    scan_id: Optional[int]
    locations: List[Location]
    created: datetime
    image_path: Optional[str] = None

class ScanStatusFile(BaseModel):
    progress: float

class MicroscopeUpdate(BaseModel):
    state: Dict[str, Any]
