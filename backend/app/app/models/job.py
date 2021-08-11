from sqlalchemy import JSON, Column, Enum, ForeignKey, Integer, String

from app.db.base_class import Base
from app.schemas.job import JobState


class Job(Base):
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String)
    slurm_id = Column(Integer, index=True, nullable=True)
    state = Column(Enum(JobState), default=JobState.INITIALIZING, nullable=True)
    params = Column(JSON)
    output = Column(String, nullable=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
