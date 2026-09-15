import logging
from sqlalchemy.dialects.postgresql import insert

from db.connection import Base, engine, SessionLocal
from db.locations_data import CITIES_TO_ADD
from db.models import Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_and_seed():
    """Initializes table schema and seeds the default locations into PostgreSQL."""
    logger.info("Ensuring database schema exists...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        inserted = 0
        for city in CITIES_TO_ADD:
            stmt = (
                insert(Location)
                .values(
                    name=city["name"],
                    country=city["country"],
                    region=city.get("region"),
                    latitude=city["latitude"],
                    longitude=city["longitude"],
                )
                .on_conflict_do_nothing(index_elements=["latitude", "longitude"])
            )
            res = db.execute(stmt)
            if res.rowcount > 0:
                inserted += 1
        db.commit()
        logger.info(
            "Database initialized. Seeded %d new locations (out of %d configured).", inserted, len(CITIES_TO_ADD)
        )
    except Exception as e:
        db.rollback()
        logger.error("Failed to seed locations: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_and_seed()
