from api.weather_client import get_weather

def fetch_weather(lat, lon):
    data = get_weather(lat, lon)

    current = data.get("current_weather", {})
    hourly = data.get("hourly", {})

    if not hourly:
        raise ValueError("No hourly data returned from API")

    i = -1  # latest index

    return {
        "temperature": current.get("temperature"),
        "wind_speed": current.get("windspeed"),
        "time": current.get("time"),

        "pressure": hourly["pressure_msl"][i],
        "humidity": hourly["relative_humidity_2m"][i]
    }