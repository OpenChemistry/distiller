from sqlalchemy import Column, String

from app.db.base_class import Base


class User(Base):
    username = Column(String, primary_key=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
