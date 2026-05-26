from services.weather_service import fetch_weather
from services.location_service import get_or_create_location
from db.connection import SessionLocal
from utilities.logger import logger
from services.save_weather import save_weather
from services.snowflake_loader import load_weather_to_snowflake
from db.snowflake_connection import get_snowflake_connection

def run(lat, lon):
    logger.info(f"Fetching weather for lat={lat}, lon={lon}")

    db = SessionLocal()
    conn = get_snowflake_connection()
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
            row["location_id"] = location.id
            save_weather(row)

        logger.info(f"Processed {len(rows)} weather records")

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

        load_weather_to_snowflake(conn, snowflake_rows)
    
    except Exception as e:
        logger.exception("Error occurred while processing weather")
        logger.error(f"Failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    run(33.6405, -117.6026)