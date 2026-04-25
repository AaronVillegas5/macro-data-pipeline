from sqlalchemy import Column, Integer, String
from db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class Weather(Base):
    __tablename__ = 'weather'