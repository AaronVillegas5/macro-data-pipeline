from api.weather_client import get_weather

def fetch_weather(lat, lon):
    # Get JSON data from API
    data = get_weather(lat, lon)

    hourly = data.get("hourly", {})
    times = hourly["time"]

    rows = []

    for i in range(len(times)):
        rows.append({
            "temperature_c": hourly["temperature_2m"][i],
            "wind_speed": hourly["windspeed_10m"][i],
            "pressure": hourly["pressure_msl"][i],
            "humidity": hourly["relative_humidity_2m"][i],
            "observed_at": times[i]
        })
    
    return rows