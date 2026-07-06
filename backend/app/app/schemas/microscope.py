from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class Microscope(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    config: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class MicroscopeUpdate(BaseModel):
    state: Dict[str, Any]


class MicroscopeEventType(str, Enum):
    UPDATED = "microscope.updated"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class MicroscopeUpdateEvent(BaseModel):
    event_type: str = MicroscopeEventType.UPDATED
    id: int
    state: Dict[str, Any]
