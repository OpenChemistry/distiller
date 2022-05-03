from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models


def get_microscopes(
    db: Session
):

    return db.query(models.Microscope).order_by(desc(models.Job.id).all())


