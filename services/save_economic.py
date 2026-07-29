from db.connection import SessionLocal
from db.models import EconomicObservation
from sqlalchemy.dialects.postgresql import insert
import os
from google.cloud import bigquery


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
def save_economic_to_bigquery(data: dict) -> None:
    """Stream economic observations into BigQuery."""
    project_id = os.environ.get("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.economic_data.observations_v2"
    observed_at = data.get("observed_at")
    row = {
        "series_id": data["series_id"],
        "series_name": data.get("series_name", ""),
        "value": float(data["value"]),
        "observed_at": observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at),
    }
    errors = client.insert_rows_json(table_ref, [row])
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")