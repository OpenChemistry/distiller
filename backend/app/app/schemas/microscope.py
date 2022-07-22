from typing import Any, Dict, Optional

from pydantic import BaseModel


class Microscope(BaseModel):
    id: int
    name: str
    config: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True
