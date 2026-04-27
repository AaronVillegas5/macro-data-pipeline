from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class WeatherObservation(Base):
    __tablename__ = "weather_observations"
    __table_args__ = (
        UniqueConstraint("location_id", "observed_at", name="unique_location_time"),
    )

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

class EconomicObservation(Base):
    __tablename__ = "economic_observations"
    __table_args__ = (
        UniqueConstraint("series_id", "observed_at", name="unique_series_time"),
        )

    id = Column(Integer, primary_key=True, nullable=False)

    series_name = Column(String)

    series_id = Column(String, nullable= False)

    value = Column(Float, nullable=False)

    observed_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

# class RetailObservation(Base):
#     __tablename__ = "retail_observations"
#     id = Column(Integer, primary_key=True, nullable=False)
class RawApiResponse(Base):
    __tablename__ = "raw_api_responses"

    id = Column(Integer, primary_key=True, nullable=False)
    source = Column(String(50), nullable=False)
    identifier = Column(String(100))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_response = Column(JSONB, nullable=False)
