from sqlalchemy import Column, DateTime, Integer, String, ForeignKey

from app.db.base_class import Base


class Location(Base):
    id = Column(Integer, primary_key=True, index=True)
    host = Column(String)
    path = Column(String)
    scan_id = Column(Integer, ForeignKey('scans.id'))