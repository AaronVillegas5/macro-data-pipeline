from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True)

    temperature_c = Column(Float)

    wind_speed = Column(Float)

    observed_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())