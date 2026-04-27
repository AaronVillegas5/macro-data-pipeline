from db.connection import SessionLocal
from db.models import EconomicObservation
from sqlalchemy.dialects.postgresql import insert


def save_economic(data):
    db = SessionLocal()

    try:
        stmt = insert(EconomicObservation).values(
            series_id = data["series_id"],
            value = data["value"],
            observed_at = data["observed_at"]
        )

        stmt = stmt.on_conflict_do_nothing(
            index_elements=["series_id", "observed_at"]
        )

        db.execute(stmt)
        db.commit()

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()