from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


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
    src_path: str
    is_directory: bool
    created: datetime = None
    host: str
    content: Optional[str] = None


class File(BaseModel):
    path: str
    created: datetime = None
    host: str
    content: Optional[str] = None


class SyncEvent(BaseModel):
    microscope_id: Optional[int]
    files: List[File]


class HaadfUploaded(BaseModel):
    scan_id: int
    path: str


class ScanFileUploaded(BaseModel):
    id: int
    path: str
    # This is the original filename
    filename: str
