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
