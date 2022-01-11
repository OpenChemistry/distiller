from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import oauth2_password_bearer_or_api_key, get_api_key
from app.core.config import settings
from app import schemas


router = APIRouter()


@router.get(
    "",
    response_model=List[str],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_machines():
    machines = [m.name for m in settings.MACHINES]

    return machines

@router.get(
    "/{name}",
    response_model=schemas.Machine,
    dependencies=[Depends(get_api_key)],
)
def read_machine(name: str):

    for m in settings.MACHINES:
        if m.name == name:
            return m

    raise HTTPException(status_code=404, detail="Machine not found")