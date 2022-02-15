from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api.deps import get_api_key, oauth2_password_bearer_or_api_key
from app.core.config import settings
from app.core.constants import NERSC_STATUS_URL_PREFIX

router = APIRouter()


@router.get(
    "",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_machines():
    machines = [{"name": m.name, "statusURL": f"{NERSC_STATUS_URL_PREFIX}{m.name}"} for m in settings.MACHINES]

    return machines


@router.get(
    "/{name}",
    response_model=schemas.Machine,
    response_model_exclude_none=True,
    dependencies=[Depends(get_api_key)],
)
def read_machine(name: str):

    for m in settings.MACHINES:
        if m.name == name:
            return m

    raise HTTPException(status_code=404, detail="Machine not found")
