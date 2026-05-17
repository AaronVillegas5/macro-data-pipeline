from db.connection import SessionLocal
from db.models import WeatherObservation
from sqlalchemy.dialects.postgresql import insert


def save_weather(data):
    db = SessionLocal()

    try:
        stmt = insert(WeatherObservation).values(
            location_id=data["location_id"],
            temperature_c=data["temperature_c"],
            wind_speed=data["wind_speed"],
            observed_at=data["observed_at"],
            pressure=data["pressure"],
            humidity=data["humidity"]
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["location_id", "observed_at"],
            set_={
                "temperature_c": stmt.excluded.temperature_c,
                "wind_speed": stmt.excluded.wind_speed,
                "pressure": stmt.excluded.pressure,
                "humidity": stmt.excluded.humidity,
            }
        )

        db.execute(stmt)
        db.commit()

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()