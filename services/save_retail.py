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

def save_retail_to_postgres(data) -> None:
    db = SessionLocal()
    # Normalize to a list
    observations = data if isinstance(data, list) else [data]
    
    try:
        for d in observations:
            stmt = insert(RetailObservation).values(
                naics_code=d["naics_code"],
                category_name=d["category_name"],
                value=d["value"],
                observed_at=d["observed_at"]
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

def save_retail_to_bigquery(data) -> None:
    project_id = os.environ.get("BIGQUERY_PROJECT_ID")
    if not project_id:
        raise EnvironmentError("BIGQUERY_PROJECT_ID environment variable is not set.")

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{_BQ_DATASET}.{_BQ_TABLE}"

    observations = data if isinstance(data, list) else [data]
    rows = []
    
    for d in observations:
        observed_at = d.get("observed_at")
        rows.append({
            "naics_code": d["naics_code"],
            "category_name": d["category_name"],
            "value": d["value"],
            "observed_at": observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at)
        })

    # Use a LoadJob instead of Streaming API to bypass the 10-year partition limit
    import json
    import io
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    
    json_data = "\n".join(json.dumps(row) for row in rows)
    file_obj = io.StringIO(json_data)
    
    job = client.load_table_from_file(file_obj, table_ref, job_config=job_config)
    job.result() # Wait for job completion

def save_retail(data) -> None:
    """Orchestrates writing retail data to both PostgreSQL and BigQuery with error isolation."""
    try:
        save_retail_to_postgres(data)
    except Exception as e:
        logger.warning("PostgreSQL retail sink failed, continuing to BigQuery. Error: %s", e)

    try:
        save_retail_to_bigquery(data)
    except Exception as e:
        logger.warning("BigQuery retail sink failed. Error: %s", e)
