from services.weather_service import fetch_weather
from db.models import WeatherObservation
from services.location_service import get_or_create_location
from db.connection import SessionLocal
from utilities.logger import logger
from services.snowflake_loader import load_weather_to_snowflake

def run(lat, lon):
    """
    Fetch current weather data for given lat/lon, save to Postgres and Snowflake.
    """
    logger.info(f"Fetching weather for lat={lat}, lon={lon}")
    db = SessionLocal()

    try:
        rows = fetch_weather(lat, lon)

        location = get_or_create_location(
            db,
            name="Rancho Santa Margarita",
            country="US",
            region="CA",
            lat=lat,
            lon=lon
        )
        for row in rows:
        
            record = WeatherObservation(
                location_id=location.id,
                temperature_c=row["temperature_c"],
                wind_speed=row["wind_speed"],
                observed_at=row["observed_at"],
                pressure=row["pressure"],
                humidity=row["humidity"]
            )

            db.add(record)
        db.commit()
        logger.info(f"Inserted {len(rows)} weather records")

        snowflake_rows = [{
            "latitude": lat,
            "longitude": lon,
            "observed_at": row["observed_at"],
            "temperature": row["temperature_c"],
            "precipitation": row.get("precipitation", 0.0)
        } for row in rows]

        load_weather_to_snowflake(snowflake_rows)
        

    except Exception as e:
        db.rollback()
        logger.exception("Error occurred while saving weather")        
        logger.error(f"Database insert failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    run(33.6405, -117.6026) #Irvine