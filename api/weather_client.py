import requests, time
from requests.exceptions import RequestException
from utilities.logger import logger
from db.connection import SessionLocal
from services.s3_client import save_raw_response
from datetime import datetime, timezone

def get_weather(lat, lon):
    logger.info("Calling Open-Meteo API")

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "pressure_msl,windspeed_10m,temperature_2m,relative_humidity_2m",
        "forecast_days": 1
    }

    last_error = None

    for attempt in range(5):  # increase retries for flaky network
        try:
            response = requests.get(url, params=params, timeout=(5, 30))
            response.raise_for_status()
            data = response.json()
            break

        except RequestException as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning(f"Attempt {attempt+1} failed: {e}. retrying in {wait}s")
            time.sleep(wait)

    else:
        raise RuntimeError(f"Open-Meteo failed after retries: {last_error}")

    location_key = f"{lat}_{lon}"
    db = SessionLocal()

    now = datetime.now(timezone.utc)

    try:
        save_raw_response(
            "weather",
            location_key,
            data,
            db,
            start=now.isoformat(),
            end=now.isoformat()
        )
    finally:
        db.close()

    return data