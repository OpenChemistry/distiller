from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models


def get_microscopes(db: Session):

    return db.query(models.Microscope).order_by(desc(models.Microscope.id)).all()
