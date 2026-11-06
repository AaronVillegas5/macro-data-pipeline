from api.weather_client import get_weather


def fetch_weather(lat, lon):
    # Get JSON data from API
    data = get_weather(lat, lon)

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    precip = hourly.get("precipitation", [])

    rows = []

    for i in range(len(times)):
        p_val = precip[i] if i < len(precip) and precip[i] is not None else 0.0
        rows.append(
            {
                "temperature_c": hourly["temperature_2m"][i],
                "wind_speed": hourly["windspeed_10m"][i],
                "pressure": hourly["pressure_msl"][i],
                "humidity": hourly["relative_humidity_2m"][i],
                "precipitation": float(p_val),
                "observed_at": times[i],
            }
        )

    return rows
