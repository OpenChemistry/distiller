from sqlalchemy import ForeignKey, Column, Table
from app.db.base_class import Base

scan_job_table = Table(
    "scan_job_table",
    Base.metadata,
    Column("scan_id", ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True),
    Column("job_id", ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
)