"""migrate_historical_economic.py
Streams all EconomicObservation rows from PostgreSQL into BigQuery (economic_data.observations_v2).
"""
import os
import sys
import logging
from dotenv import load_dotenv
from google.cloud import bigquery

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.connection import SessionLocal
from db.models import EconomicObservation

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_BQ_DATASET = "economic_data"
_BQ_TABLE = "observations_v2"

def main():
    project_id = os.environ.get("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    key_path = os.path.join(os.path.dirname(__file__), "..", "gcp-key.json")
    if os.path.exists(key_path):
        client = bigquery.Client.from_service_account_json(key_path, project=project_id)
    else:
        client = bigquery.Client(project=project_id)

    table_ref = f"{project_id}.{_BQ_DATASET}.{_BQ_TABLE}"

    db = SessionLocal()
    try:
        observations = db.query(EconomicObservation).all()
        logger.info(f"Found {len(observations)} economic rows in PostgreSQL.")

        if not observations:
            logger.info("No economic rows to migrate.")
            return

        rows = []
        for obs in observations:
            rows.append({
                "series_id": obs.series_id,
                "series_name": obs.series_name or "",
                "value": float(obs.value),
                "observed_at": obs.observed_at.isoformat() if hasattr(obs.observed_at, "isoformat") else str(obs.observed_at),
            })

        # Use Batch Load Job instead of streaming inserts to bypass BigQuery's 10-year streaming limit
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("series_id", "STRING"),
                bigquery.SchemaField("series_name", "STRING"),
                bigquery.SchemaField("value", "FLOAT"),
                bigquery.SchemaField("observed_at", "TIMESTAMP"),
            ],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        logger.info(f"Submitting batch load job for {len(rows)} economic rows...")
        job = client.load_table_from_json(rows, table_ref, job_config=job_config)
        job.result()  # Wait for completion

        logger.info("Economic batch migration completed successfully!")


    finally:
        db.close()

if __name__ == "__main__":
    main()
