from services.weather_service import fetch_weather
from db.models import WeatherObservation
from services.location_service import get_or_create_location
from db.connection import SessionLocal
from utilities.logger import logger

def run(lat, lon):
    logger.info(f"Fetching weather for lat={lat}, lon={lon}")
    db = SessionLocal()

    try:
        data = fetch_weather(lat, lon)

        location = get_or_create_location(
            db,
            name="Rancho Santa Margarita",
            country="US",
            region="CA",
            lat=lat,
            lon=lon
        )

        record = WeatherObservation(
            location_id=location.id,
            temperature_c=data["temperature"],
            wind_speed=data["wind_speed"],
            observed_at=data["time"],
            pressure=data["pressure"],
            humidity=data["humidity"]
        )

        db.add(record)
        db.commit()
        logger.info(f"Inserted weather record id={record.id}")

    except Exception as e:
        db.rollback()
        logger.exception("Error occurred while saving weather")        
        logger.error(f"Database insert failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    run(33.6405, -117.6026) #Irvine