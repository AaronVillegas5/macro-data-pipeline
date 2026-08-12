import os
from google.cloud import bigquery
from google.oauth2 import service_account

# Path to the service account key
key_path = os.path.join(os.path.dirname(__file__), '..', 'gcp-key.json')

# Authenticate using the service account key
credentials = service_account.Credentials.from_service_account_file(key_path)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Define the query
query = """
SELECT 
  COUNT(*) as total_rows,
  COUNT(precipitation) as non_null_precipitation_rows
FROM `macro-data-pipeline-498302.weather_data.observations_v2`
WHERE precipitation IS NOT NULL AND precipitation > 0;
"""

print("Running query on BigQuery...")
# Run the query
query_job = client.query(query)
results = query_job.result()

# Print the results
for row in results:
    print(f"Total Rows > 0 Precip: {row.total_rows}")
    print(f"Non-Null Precip Rows: {row.non_null_precipitation_rows}")
