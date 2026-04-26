from db.connection import SessionLocal
from db.models import WeatherObservation

def save_weather(data):
    db = SessionLocal()
    try:
        record = WeatherObservation(
            temperature_c=data["temperature"],
            wind_speed=data["wind_speed"],
            observed_at=data["time"]
        )

        db.add(record)
        db.commit()

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()