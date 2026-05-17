import requests, time
from utilities.logger import logger
from services.s3_client import save_raw_response
from db.connection import SessionLocal

# First step of pipeline
# Fetch weather data from Open-Meteo API with retries and save raw response to S3
def get_weather(lat, lon):
    logger.info("Calling Open-Meteo API")
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "pressure_msl,windspeed_10m,temperature_2m,relative_humidity_2m"  # Can be adjusted based on needs, will have to change db schema and models.py
    }

    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            break

        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")

            if attempt == 2:
                raise

            time.sleep(5)    
    response.raise_for_status()

    data = response.json()
    location_key = f"{lat}_{lon}"
    db = SessionLocal()
    try:
        save_raw_response("weather", location_key, data, db)
    finally:
        db.close()            # always close even if save fails
    return data