from typing import Optional

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app import models


def get_microscopes(db: Session, name: Optional[str] = None):

    query = db.query(models.Microscope)

    if name is not None:
        query = query.filter(models.Microscope.name == name)

    return query.order_by(asc(models.Microscope.id)).all()


def get_microscope(db: Session, id: int):
    return db.query(models.Microscope).filter(models.Microscope.id == id).first()