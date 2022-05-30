from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_db, oauth2_password_bearer_or_api_key
from app.crud import microscope as crud

router = APIRouter()


@router.get(
    "",
    response_model=List[schemas.Microscope],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_microscopes(
    name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    microscopes = crud.get_microscopes(db, name=name)

    return microscopes
