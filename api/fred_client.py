import requests, os
from utilities.logger import logger
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('FRED_API_KEY')


def get_series(series_id):
    if not API_KEY:
        raise ValueError("Missing FRED_API_KEY in .env")
    logger.info(f"Calling FRED API for {series_id}")
    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json() 