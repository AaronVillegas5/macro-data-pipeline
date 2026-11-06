import logging
import os

# pyrefly: ignore [missing-import]
from google.cloud import bigquery
from sqlalchemy.dialects.postgresql import insert

from db.connection import SessionLocal
from db.models import WeatherObservation

logger = logging.getLogger(__name__)

# BigQuery constants
_BQ_DATASET = "weather_data"
_BQ_TABLE = "observations_v2"


# ---------------------------------------------------------------------------
# Sink 1: PostgreSQL
# ---------------------------------------------------------------------------


def save_weather_to_postgres(data) -> None:
    """
    Upserts weather observation(s) into PostgreSQL using ON CONFLICT DO UPDATE.
    Supports either a single observation dict or a batch list of dicts.
    """
    observations = data if isinstance(data, list) else [data]
    if not observations:
        return

    db = SessionLocal()

    try:
        for d in observations:
            stmt = insert(WeatherObservation).values(
                location_id=d["location_id"],
                temperature_c=d["temperature_c"],
                wind_speed=d["wind_speed"],
                observed_at=d["observed_at"],
                pressure=d["pressure"],
                humidity=d["humidity"],
                precipitation=d.get("precipitation", 0.0),
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=["location_id", "observed_at"],
                set_={
                    "temperature_c": stmt.excluded.temperature_c,
                    "wind_speed": stmt.excluded.wind_speed,
                    "pressure": stmt.excluded.pressure,
                    "humidity": stmt.excluded.humidity,
                    "precipitation": stmt.excluded.precipitation,
                },
            )

            db.execute(stmt)
        db.commit()
        logger.debug(
            "PostgreSQL: upserted %d observations",
            len(observations),
        )

    except Exception as e:
        db.rollback()
        logger.error("PostgreSQL write failed: %s", e, exc_info=True)
        raise

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Sink 2: BigQuery
# ---------------------------------------------------------------------------


def save_weather_to_bigquery(data) -> None:
    """Stream weather observation(s) into BigQuery in a single batch request."""
    project_id = os.environ.get("BIGQUERY_PROJECT_ID")
    if not project_id:
        raise OSError("BIGQUERY_PROJECT_ID environment variable is not set.")

    observations = data if isinstance(data, list) else [data]
    if not observations:
        return

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{_BQ_DATASET}.{_BQ_TABLE}"

    rows = []
    for d in observations:
        observed_at = d.get("observed_at")
        rows.append(
            {
                "location_id": d["location_id"],
                "temperature_c": d["temperature_c"],
                "wind_speed": d["wind_speed"],
                "observed_at": observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at),
                "pressure": d["pressure"],
                "humidity": d["humidity"],
                "precipitation": float(d.get("precipitation") or 0.0),
            }
        )

    errors = client.insert_rows_json(table_ref, rows)

    if errors:
        raise RuntimeError(f"BigQuery streaming insert errors: {errors}")

    logger.debug("BigQuery: streamed %d observations", len(rows))


# ---------------------------------------------------------------------------
# Orchestrator — dual-sink with independent error isolation
# ---------------------------------------------------------------------------


def save_weather(data) -> None:
    """Write weather observation(s) to both PostgreSQL and BigQuery.

    Supports either a single observation dict or a list of observation dicts.
    """
    try:
        save_weather_to_postgres(data)
    except Exception as e:
        logger.warning("PostgreSQL sink failed, continuing to BigQuery. Error: %s", e)

    try:
        save_weather_to_bigquery(data)
    except Exception as e:
        logger.warning("BigQuery sink failed. Error: %s", e)
