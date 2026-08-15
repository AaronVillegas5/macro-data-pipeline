import os
import sys
import csv

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.connection import engine, SessionLocal, Base
from db.models import Location, WeatherObservation, EconomicObservation, RawApiResponse, User
from utilities.logger import logger

def init_database():
    logger.info("Creating database tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

    # Seed locations from locations.csv if table is empty
    db = SessionLocal()
    try:
        count = db.query(Location).count()
        if count == 0:
            csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "locations.csv"))
            if os.path.exists(csv_path):
                logger.info(f"Seeding locations from {csv_path}...")
                with open(csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        loc = Location(
                            id=int(row["id"]),
                            name=row["name"],
                            country=row["country"],
                            region=row["region"],
                            latitude=float(row["latitude"]),
                            longitude=float(row["longitude"])
                        )
                        db.merge(loc)
                db.commit()
                logger.info("Locations seeded successfully.")
            else:
                logger.warning(f"locations.csv not found at {csv_path}")
        else:
            logger.info(f"Locations table already has {count} records. Skipping seed.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding locations: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
