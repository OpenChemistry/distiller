from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    hashed_password: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    username: str
    full_name: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    username: str
    full_name: Optional[str] = None
