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


def save_weather_to_postgres(data: dict) -> None:
    """
    Upserts a single weather observation into PostgreSQL using ON CONFLICT DO UPDATE.

    Data Validation & Edge Cases:
    - Null values and missing timeseries data in mutable fields (e.g., pressure, humidity) will safely
      overwrite existing records if an update occurs.
    - Time-Series Gaps: Resolves historical gaps by allowing missing observations to be backfilled safely
      without duplicating existing data points.

    Cloud Destination (PostgreSQL):
    - Uses SQLAlchemy's PostgreSQL dialect `insert().on_conflict_do_update()`.
    - Conflicts on the unique composite index (location_id, observed_at) trigger an update of mutable fields.
    - Ensures atomicity through transaction rollbacks on failure.
    """
    db = SessionLocal()

    try:
        stmt = insert(WeatherObservation).values(
            location_id=data["location_id"],
            temperature_c=data["temperature_c"],
            wind_speed=data["wind_speed"],
            observed_at=data["observed_at"],
            pressure=data["pressure"],
            humidity=data["humidity"],
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["location_id", "observed_at"],
            set_={
                "temperature_c": stmt.excluded.temperature_c,
                "wind_speed": stmt.excluded.wind_speed,
                "pressure": stmt.excluded.pressure,
                "humidity": stmt.excluded.humidity,
            },
        )

        db.execute(stmt)
        db.commit()
        logger.debug(
            "PostgreSQL: upserted observation for location_id=%s",
            data.get("location_id"),
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


def save_weather_to_bigquery(data: dict) -> None:
    """Stream a single weather observation into BigQuery.

    Targets: <BIGQUERY_PROJECT_ID>.weather_data.observations

    The table must already exist in BigQuery with a compatible schema.
    BigQuery streaming inserts are eventually consistent and do not support
    true upserts — duplicate rows may appear if this function is retried.
    """
    project_id = os.environ.get("BIGQUERY_PROJECT_ID")
    if not project_id:
        raise OSError("BIGQUERY_PROJECT_ID environment variable is not set.")

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{_BQ_DATASET}.{_BQ_TABLE}"

    # BigQuery's insert_rows_json requires JSON-serialisable values.
    # Convert datetime → ISO-8601 string so the transport layer is happy.
    observed_at = data.get("observed_at")
    row = {
        "location_id": data["location_id"],
        "temperature_c": data["temperature_c"],
        "wind_speed": data["wind_speed"],
        "observed_at": observed_at.isoformat()
        if hasattr(observed_at, "isoformat")
        else str(observed_at),
        "pressure": data["pressure"],
        "humidity": data["humidity"],
    }

    errors = client.insert_rows_json(table_ref, [row])

    if errors:
        raise RuntimeError(f"BigQuery streaming insert errors: {errors}")

    logger.debug(
        "BigQuery: streamed observation for location_id=%s", data.get("location_id")
    )


# ---------------------------------------------------------------------------
# Orchestrator — dual-sink with independent error isolation
# ---------------------------------------------------------------------------


def save_weather(data: dict) -> None:
    """Write a weather observation to both PostgreSQL and BigQuery.

    Each sink is wrapped in its own try/except so that a failure in one
    does not prevent the other from writing.  Both failures are logged;
    individual exceptions are re-raised only within their own block.
    """
    try:
        save_weather_to_postgres(data)
    except Exception as e:
        # Error already logged inside save_weather_to_postgres; swallow here
        # so BigQuery write still proceeds.
        logger.warning("PostgreSQL sink failed, continuing to BigQuery. Error: %s", e)

    try:
        save_weather_to_bigquery(data)
    except Exception as e:
        # Swallow so a BigQuery outage never blocks the Postgres path.
        logger.warning("BigQuery sink failed. Error: %s", e)
