from api.client import get_weather

def fetch_weather(lat, lon):
    data = get_weather(lat, lon)

    current = data["current_weather"]

    return {
        "temperature": current["temperature"],
        "wind_speed": current["windspeed"],
        "time": current["time"]
    }