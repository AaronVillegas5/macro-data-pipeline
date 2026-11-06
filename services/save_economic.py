import logging
import os

from google.cloud import bigquery
from sqlalchemy.dialects.postgresql import insert

from db.connection import SessionLocal
from db.models import EconomicObservation

logger = logging.getLogger(__name__)

_BQ_DATASET = "economic_data"
_BQ_TABLE = "observations_v2"


def save_economic_to_postgres(data) -> None:
    """Upserts economic observation(s) into PostgreSQL using ON CONFLICT DO UPDATE.

    Supports either a single observation dict or a batch list of dicts.
    """
    observations = data if isinstance(data, list) else [data]
    if not observations:
        return

    db = SessionLocal()
    try:
        for d in observations:
            stmt = insert(EconomicObservation).values(
                series_id=d["series_id"],
                series_name=d.get("series_name", ""),
                value=d["value"],
                observed_at=d["observed_at"],
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["series_id", "observed_at"],
                set_={
                    "series_name": stmt.excluded.series_name,
                    "value": stmt.excluded.value,
                },
            )
            db.execute(stmt)
        db.commit()
        logger.debug("PostgreSQL: upserted %d economic observations", len(observations))
    except Exception as e:
        db.rollback()
        logger.error("PostgreSQL economic write failed: %s", e)
        raise
    finally:
        db.close()


def save_economic_to_bigquery(data) -> None:
    """Batch loads economic observation(s) into BigQuery."""
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
                "series_id": d["series_id"],
                "series_name": d.get("series_name", ""),
                "value": float(d["value"]),
                "observed_at": observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at),
            }
        )

    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("series_id", "STRING"),
            bigquery.SchemaField("series_name", "STRING"),
            bigquery.SchemaField("value", "FLOAT"),
            bigquery.SchemaField("observed_at", "TIMESTAMP"),
        ],
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    job.result()
    logger.debug("BigQuery: loaded %d economic observations", len(rows))


def save_economic(data) -> None:
    """Orchestrates writing economic data to both PostgreSQL and BigQuery with error isolation."""
    try:
        save_economic_to_postgres(data)
    except Exception as e:
        logger.warning("PostgreSQL economic sink failed, continuing to BigQuery. Error: %s", e)

    try:
        save_economic_to_bigquery(data)
    except Exception as e:
        logger.warning("BigQuery economic sink failed. Error: %s", e)
