"""migrate_historical_weather.py

One-time migration script: reads all WeatherObservation rows from PostgreSQL
and streams them into BigQuery (weather_data.observations).

Usage:
    python scripts/migrate_historical_weather.py [--batch-size 500] [--dry-run]

Prerequisites:
    1. BIGQUERY_PROJECT_ID must be set in your environment (or .env file).
    2. Application Default Credentials (ADC) must be configured:
           gcloud auth application-default login
    3. The BigQuery table `<project>.weather_data.observations` must already
       exist with a schema compatible with WeatherObservation.

Notes:
    - BigQuery streaming inserts are eventually consistent.
    - Re-running this script may produce duplicate rows in BigQuery.
    - Use BigQuery's MERGE statement (or create the table with deduplication)
      if idempotency is required after the fact.
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from google.cloud import bigquery
from sqlalchemy.orm import Session

# Make sure the project root is on the path when running the script directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.connection import SessionLocal
from db.models import WeatherObservation

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_BQ_DATASET = "weather_data"
_BQ_TABLE = "observations"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _observation_to_bq_row(obs: WeatherObservation) -> dict:
    """Serialise a WeatherObservation ORM instance into a BigQuery-safe dict."""
    return {
        "location_id": obs.location_id,
        "temperature_c": obs.temperature_c,
        "wind_speed": obs.wind_speed,
        "pressure": obs.pressure,
        "humidity": obs.humidity,
        "observed_at": obs.observed_at.isoformat() if obs.observed_at else None,
        "created_at": obs.created_at.isoformat() if obs.created_at else None,
    }


def _stream_batch(client: bigquery.Client, table_ref: str, rows: list[dict], dry_run: bool) -> int:
    """Stream a list of row dicts to BigQuery. Returns the number of errors."""
    if dry_run:
        logger.info("[DRY-RUN] Would stream %d rows to %s", len(rows), table_ref)
        return 0

    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        logger.error("BigQuery insert errors in batch: %s", errors)
        return len(errors)
    return 0


# ---------------------------------------------------------------------------
# Main migration logic
# ---------------------------------------------------------------------------

def migrate(batch_size: int = 500, dry_run: bool = False) -> None:
    project_id = os.environ.get("BIGQUERY_PROJECT_ID")
    if not project_id:
        raise EnvironmentError(
            "BIGQUERY_PROJECT_ID environment variable is not set. "
            "Add it to your .env file or export it before running this script."
        )

    table_ref = f"{project_id}.{_BQ_DATASET}.{_BQ_TABLE}"
    logger.info("Target BigQuery table: %s", table_ref)
    logger.info("Batch size: %d  |  Dry-run: %s", batch_size, dry_run)

    bq_client = bigquery.Client(project=project_id)
    db: Session = SessionLocal()

    try:
        total_rows = db.query(WeatherObservation).count()
        logger.info("Found %d WeatherObservation rows in PostgreSQL.", total_rows)

        if total_rows == 0:
            logger.info("Nothing to migrate. Exiting.")
            return

        migrated = 0
        total_errors = 0
        offset = 0

        while True:
            batch_orm = (
                db.query(WeatherObservation)
                .order_by(WeatherObservation.id)
                .offset(offset)
                .limit(batch_size)
                .all()
            )

            if not batch_orm:
                break  # No more rows

            rows = [_observation_to_bq_row(obs) for obs in batch_orm]
            error_count = _stream_batch(bq_client, table_ref, rows, dry_run)
            total_errors += error_count
            migrated += len(rows)
            offset += batch_size

            logger.info(
                "Progress: %d / %d rows streamed  (errors in this batch: %d)",
                migrated,
                total_rows,
                error_count,
            )

        logger.info(
            "Migration complete. Total rows processed: %d | Total BigQuery errors: %d",
            migrated,
            total_errors,
        )

        if total_errors > 0:
            logger.warning(
                "%d rows failed to insert. Check the error log above and consider re-running.",
                total_errors,
            )

    finally:
        db.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate historical WeatherObservation rows from PostgreSQL to BigQuery."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of rows to stream per BigQuery API call (default: 500).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Walk through PostgreSQL rows and log counts without writing to BigQuery.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    migrate(batch_size=args.batch_size, dry_run=args.dry_run)
