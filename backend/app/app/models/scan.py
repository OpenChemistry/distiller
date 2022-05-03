from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Scan(Base):
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, index=True)
    log_files = Column(Integer, default=0)
    created = Column(DateTime(timezone=True), nullable=False, index=True)
    haadf_path = Column(String, nullable=True, default=None, index=True)
    notes = Column(String, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    microscope_id = Column(Integer, ForeignKey("microscopes.id"), nullable=False, index=True, default=1)

    locations = relationship("Location", cascade="delete")
    jobs = relationship("Job", cascade="delete")

    __table_args__ = (UniqueConstraint("scan_id", "created", name="scan_id_created"),)
