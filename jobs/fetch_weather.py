from services.weather_service import fetch_weather
from db.connection import SessionLocal
from db.models import Location
from utilities.logger import logger
from services.save_weather import save_weather
from services.snowflake_loader import load_weather_to_snowflake
from db.snowflake_connection import get_snowflake_connection

def fetch_weather_for_location(db, conn, location: Location):
    """Fetches and saves weather observations for a specific Location record."""
    lat, lon = location.latitude, location.longitude
    logger.info(f"Fetching weather for {location.name} (id={location.id}, lat={lat}, lon={lon})")

    rows = fetch_weather(lat, lon)
    if not rows:
        logger.warning(f"No weather records returned for {location.name}")
        return

    for row in rows:
        row["location_id"] = location.id
        save_weather(row)

    logger.info(f"Processed {len(rows)} weather records for {location.name}")

    snowflake_rows = [
        {
            "latitude": lat,
            "longitude": lon,
            "observed_at": row["observed_at"],
            "temperature": row["temperature_c"],
            "precipitation": row.get("precipitation", 0.0)
        }
        for row in rows
    ]

    if conn:
        try:
            load_weather_to_snowflake(conn, snowflake_rows)
        except Exception as e:
            logger.warning(f"Snowflake loader failed for {location.name}: {e}")

def run():
    """Loops through all active locations in PostgreSQL and ingests their latest weather."""
    db = SessionLocal()
    conn = None
    try:
        try:
            conn = get_snowflake_connection()
        except Exception as e:
            logger.warning(f"Could not connect to Snowflake: {e}")

        locations = db.query(Location).all()
        if not locations:
            logger.warning("No locations found in PostgreSQL database.")
            return

        logger.info(f"Starting weather ingestion for {len(locations)} locations.")
        for location in locations:
            try:
                fetch_weather_for_location(db, conn, location)
            except Exception as e:
                logger.error(f"Failed to fetch weather for {location.name}: {e}")

    except Exception as e:
        logger.exception("Error occurred while querying locations for weather processing")
    finally:
        db.close()

if __name__ == "__main__":
    run()