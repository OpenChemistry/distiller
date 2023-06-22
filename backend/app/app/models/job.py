from sqlalchemy import JSON, Column, DateTime, Enum, Integer, Interval, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.schemas.job import JobState

from .association import scan_job_table


class Job(Base):
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String)
    slurm_id = Column(Integer, index=True, nullable=True)
    state = Column(Enum(JobState), default=JobState.INITIALIZING, nullable=True)
    params = Column(JSON)
    output = Column(String, nullable=True)
    elapsed = Column(Interval, nullable=True)
    machine = Column(String, nullable=False)
    submit = Column(DateTime(timezone=True), nullable=True, index=True)
    notes = Column(String, nullable=True)
    scans = relationship("Scan", secondary=scan_job_table, back_populates="jobs")
