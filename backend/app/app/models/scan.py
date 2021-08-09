from sqlalchemy import Column, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Scan(Base):
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, index=True)
    log_files = Column(Integer, default=0)
    created = Column(DateTime, nullable=False)
    locations = relationship("Location", cascade="delete")

    __table_args__ = (UniqueConstraint("scan_id", "created", name="scan_id_created"),)
