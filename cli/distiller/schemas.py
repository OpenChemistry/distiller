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
    host: str
    src_path: str
    is_directory: bool
    created: datetime = None


class File(BaseModel):
    host: str
    path: str
    created: datetime = None


class SyncEvent(BaseModel):
    files: List[File]
