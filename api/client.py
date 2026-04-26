import requests
from utilities.logger import logger


def get_weather(lat, lon):
    logger.info("Calling Open-Meteo API")
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "pressure_msl,temperature_2m,relative_humidity_2m"
    }

    response = requests.get(url, params=params, timeout=10)

    response.raise_for_status()

    return response.json()