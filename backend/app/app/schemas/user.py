from typing import Optional

from pydantic import ConfigDict, BaseModel


class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    hashed_password: str
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    full_name: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    username: str
    full_name: Optional[str] = None
