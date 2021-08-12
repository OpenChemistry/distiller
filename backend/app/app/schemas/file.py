from datetime import datetime
from enum import Enum
from typing import List

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


class File(BaseModel):
    path: str
    created: datetime = None
    host: str


class SyncEvent(BaseModel):
    files: List[File]


class HaadfUploaded(BaseModel):
    scan_id: int
    path: str
