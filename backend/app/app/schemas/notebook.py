from typing import List, Optional, Union

from pydantic import BaseModel


class Notebook(BaseModel):
    path: str


class NotebookCreate(BaseModel):
    scan_id: int
    name: str


class NotebookCreateEvent(BaseModel):
    path: str
    name: str
    scan_id: int


class NotebookSpecification(BaseModel):
    name: str
    microscopes: Optional[List[Union[str, int]]] = None


class NotebookSpecificationResponse(BaseModel):
    name: str
    microscopes: Optional[List[int]] = None
