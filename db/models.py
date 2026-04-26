from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True)

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    temperature_c = Column(Float)
    wind_speed = Column(Float)
    pressure = Column(Float)
    humidity = Column(Float)

    observed_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())

class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("latitude", "longitude"),
    )

    id = Column(Integer, primary_key=True, nullable=False)

    name = Column(String, nullable=False)

    country = Column(String, nullable=False)

    region = Column(String)

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)