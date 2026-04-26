from services.weather_service import fetch_weather
from services.save_weather import save_weather

def run():
    data = fetch_weather(33.66,-117.8)  # Irvine, CA

    save_weather(data)

    print("Weather saved!")


if __name__ == "__main__":
    run()