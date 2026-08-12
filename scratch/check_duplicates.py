import os
from google.cloud import bigquery
from google.oauth2 import service_account

# Path to the service account key
key_path = os.path.join(os.path.dirname(__file__), '..', 'gcp-key.json')

# Authenticate using the service account key
credentials = service_account.Credentials.from_service_account_file(key_path)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

query = """
SELECT
    location_id,
    observed_at,
    observation_date,
    COUNT(*) as c
FROM `macro-data-pipeline-498302.dbt_pr_ci.stg_weather_observations`
GROUP BY 1, 2, 3
HAVING COUNT(*) > 1
LIMIT 5
"""

print("Checking duplicates in dbt_pr_ci.stg_weather_observations...")
query_job = client.query(query)
results = query_job.result()

found = False
for row in results:
    found = True
    print(f"Duplicate found: location_id={row.location_id}, observed_at={row.observed_at}, count={row.c}")

if not found:
    print("No duplicates found in stg_weather_observations!")

# Let's also check the raw table
query2 = """
SELECT
    location_id,
    observed_at,
    COUNT(*) as c
FROM `macro-data-pipeline-498302.weather_data.observations_v2`
GROUP BY 1, 2
HAVING COUNT(*) > 1
LIMIT 5
"""
print("\nChecking raw table...")
query_job2 = client.query(query2)
for row in query_job2.result():
    print(f"Raw Duplicate: location_id={row.location_id}, observed_at={row.observed_at}, count={row.c}")
