from db.connection import SessionLocal
from db.models import WeatherObservation
from sqlalchemy.exc import IntegrityError

def save_weather(data):
    db = SessionLocal()
    try:
        #check if location and time pair exists
        exists = db.query(WeatherObservation).filter(
            WeatherObservation.location_id == data["location_id"],
            WeatherObservation.observed_at == data["time"]
        ).first()

        if exists:
            print("Duplicate found, skipping insert")
            return
        #Only insert if not duplicate
        record = WeatherObservation(
            location_id=data["location_id"],
            temperature_c=data["temperature"],
            wind_speed=data["wind_speed"],
            observed_at=data["time"],
            pressure=data["pressure"],
            humidity=data["humidity"]
        )

        db.add(record)
        db.commit()

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()