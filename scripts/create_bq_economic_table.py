"""create_bq_economic_table.py
Creates the economic_data dataset and observations_v2 table in BigQuery.
"""
import os
import sys
from dotenv import load_dotenv
from google.cloud import bigquery

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

project_id = os.environ.get("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
key_path = os.path.join(os.path.dirname(__file__), "..", "gcp-key.json")
if os.path.exists(key_path):
    client = bigquery.Client.from_service_account_json(key_path, project=project_id)
else:
    client = bigquery.Client(project=project_id)


dataset_id = f"{project_id}.economic_data"
dataset = bigquery.Dataset(dataset_id)
dataset.location = "US"

try:
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset {dataset_id} created or already exists.")
except Exception as e:
    print(f"Error creating dataset: {e}")

table_id = f"{dataset_id}.observations_v2"
schema = [
    bigquery.SchemaField("series_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("series_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("value", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("observed_at", "TIMESTAMP", mode="REQUIRED"),
]

table = bigquery.Table(table_id, schema=schema)
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.MONTH,
    field="observed_at"
)
table.clustering_fields = ["series_id"]

try:
    # Delete table if it exists with wrong partitioning
    client.delete_table(table_id, not_found_ok=True)
    table = client.create_table(table)
    print(f"Table {table_id} recreated with MONTH partitioning.")
except Exception as e:
    print(f"Error creating table: {e}")

