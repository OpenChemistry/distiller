from typing import Optional

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    full_name: Optional[str] = None
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    full_name: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    username: str
    full_name: Optional[str] = None
