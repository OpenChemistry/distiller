from typing import List

from fastapi import APIRouter, Depends

from app.api.deps import oauth2_password_bearer_or_api_key
from app.core.config import settings

router = APIRouter()


@router.get(
    "",
    response_model=List[str],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_machines():
    machines = [m.name for m in settings.MACHINES]

    return machines
