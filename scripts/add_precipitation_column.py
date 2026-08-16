"""add_precipitation_column.py
Adds the precipitation column to BigQuery weather_data.observations_v2 table.
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

table_id = f"{project_id}.weather_data.observations_v2"
query = f"ALTER TABLE `{table_id}` ADD COLUMN IF NOT EXISTS precipitation FLOAT64;"

try:
    job = client.query(query)
    job.result()
    print(f"Successfully added precipitation column to {table_id}!")
except Exception as e:
    print(f"Error adding column: {e}")
