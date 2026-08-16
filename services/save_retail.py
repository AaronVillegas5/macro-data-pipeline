import os
import logging
from sqlalchemy.dialects.postgresql import insert
from db.connection import SessionLocal
from db.models import RetailObservation
# pyrefly: ignore [missing-import]
from google.cloud import bigquery

logger = logging.getLogger(__name__)

_BQ_DATASET = "retail_data"
_BQ_TABLE = "observations"

def save_retail_to_postgres(data: dict) -> None:
    db = SessionLocal()
    try:
        stmt = insert(RetailObservation).values(
            naics_code=data["naics_code"],
            category_name=data["category_name"],
            value=data["value"],
            observed_at=data["observed_at"]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["naics_code", "observed_at"],
            set_={
                "category_name": stmt.excluded.category_name,
                "value": stmt.excluded.value
            }
        )
        db.execute(stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("PostgreSQL retail write failed: %s", e)
        raise
    finally:
        db.close()

def save_retail_to_bigquery(data: dict) -> None:
    project_id = os.environ.get("BIGQUERY_PROJECT_ID")
    if not project_id:
        raise EnvironmentError("BIGQUERY_PROJECT_ID environment variable is not set.")

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{_BQ_DATASET}.{_BQ_TABLE}"

    observed_at = data.get("observed_at")
    row = {
        "naics_code": data["naics_code"],
        "category_name": data["category_name"],
        "value": data["value"],
        "observed_at": observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at)
    }

    errors = client.insert_rows_json(table_ref, [row])
    if errors:
        raise RuntimeError(f"BigQuery retail streaming errors: {errors}")

def save_retail(data: dict) -> None:
    """Orchestrates writing retail data to both PostgreSQL and BigQuery with error isolation."""
    try:
        save_retail_to_postgres(data)
    except Exception as e:
        logger.warning("PostgreSQL retail sink failed, continuing to BigQuery. Error: %s", e)

    try:
        save_retail_to_bigquery(data)
    except Exception as e:
        logger.warning("BigQuery retail sink failed. Error: %s", e)
