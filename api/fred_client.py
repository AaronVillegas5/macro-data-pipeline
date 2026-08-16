import os
from datetime import date

import requests
from dotenv import load_dotenv

from db.connection import SessionLocal
from services.s3_client import save_raw_response
from utilities.logger import logger

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")


def get_series(series_id):
    start = "2020-01-01"
    end = date.today().isoformat()
    if not API_KEY:
        raise ValueError("Missing FRED_API_KEY in .env")
    logger.info(f"Calling FRED API for {series_id}")
    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {"series_id": series_id, "api_key": API_KEY, "file_type": "json"}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    db = SessionLocal()
    try:
        save_raw_response("fred", series_id, data, db, start, end)
    finally:
        db.close()
    return data
