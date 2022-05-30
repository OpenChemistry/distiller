from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import Optional

from app import models


def get_microscopes(db: Session, name: Optional[str] = None):

    query = db.query(models.Microscope)

    if name is not None:
        query = query.filter(models.Microscope.name == name)

    return query.order_by(desc(models.Microscope.id)).all()
