from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint

from app.db.base_class import Base


class Location(Base):
    id = Column(Integer, primary_key=True, index=True)
    host = Column(String)
    path = Column(String)
    scan_id = Column(Integer, ForeignKey("scans.id"))

    __table_args__ = (
        UniqueConstraint("scan_id", "host", "path", name="scan_id_host_path"),
    )
