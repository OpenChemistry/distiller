from typing import Any, Dict, Optional

from pydantic import BaseModel


class Microscope(BaseModel):
    id: int
    name: str
    config: Optional[Dict[str, Any]]
    state: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True

class MicroscopeUpdate(BaseModel):
    state: Dict[str, Any]

class MicroscopeUpdateEvent(BaseModel):
    event_type: str = "microscope.updated"
    id: int
    state: Dict[str, Any]