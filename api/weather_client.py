import requests
from utilities.logger import logger
from services.s3_client import save_raw_response
from db.connection import SessionLocal


def get_weather(lat, lon):
    logger.info("Calling Open-Meteo API")
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "pressure_msl,windspeed_10m,temperature_2m,relative_humidity_2m"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    location_key = f"{lat}_{lon}"
    db = SessionLocal()
    try:
        save_raw_response("weather", location_key, data, db)
    finally:
        db.close()            # always close even if save fails
    return data