from typing import List, Optional, Any

from fastapi import APIRouter, Depends
from fastapi.security.api_key import APIKey
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_db, oauth2_password_bearer_or_api_key, get_api_key
from app.crud import microscope as crud
from app.kafka.producer import send_microscope_event_to_kafka

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


@router.get(
    "/{id}",
    response_model=schemas.Microscope,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_microscope(id: int, db: Session = Depends(get_db)):
    microscope = crud.get_microscope(db, id=id)

    return microscope


@router.patch(
    "/{id}",
    response_model=schemas.Microscope)
async def update_microscope(id: int, payload: schemas.MicroscopeUpdate, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    (updated, microscope) = crud.update_microscope(db, id=id, state=payload.state)

    if updated:
        microscope_updated_event = schemas.MicroscopeUpdateEvent(id=id, state=microscope.state)
        await send_microscope_event_to_kafka(microscope_updated_event)

    return microscope

