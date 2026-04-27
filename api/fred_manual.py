import requests, os, json
from utilities.logger import logger
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('FRED_API_KEY')

url = "https://api.stlouisfed.org/fred/series/observations"
FRED_SERIES = {
    "inflation": "CPIAUCSL",
    "unemployment": "UNRATE",
    "interest_rate": "FEDFUNDS",
    "gdp": "GDP"
}

params = {
    "series_id": FRED_SERIES,
    "api_key": API_KEY,
    "file_type": "json"
}

response = requests.get(url, params=params)

print(response.status_code)
print(json.dumps(response.json(), indent=2))