import requests
import json

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 33.6405,
    "longitude": -117.6020,
    "current_weather": True,
    "hourly": "temperature_2m,pressure_msl,relative_humidity_2m,windspeed_10m,precipitation",
    "timezone": "America/Los_Angeles"
}

response = requests.get(url, params=params)

print(response.status_code)
print(json.dumps(response.json(), indent=2))