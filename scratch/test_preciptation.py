from google.cloud import bigquery

client = bigquery.Client.from_service_account_json("gcp-key.json")

# Check precipitation stats in raw BigQuery observations
query = """
SELECT 
    location_id,
    COUNT(*) AS total_rows,
    COUNTIF(precipitation > 0) AS rainy_hours_count,
    ROUND(MAX(precipitation), 2) AS max_hourly_rain_mm,
    ROUND(SUM(precipitation), 2) AS total_rain_mm
FROM `macro-data-pipeline-498302.weather_data.observations_v2`
GROUP BY location_id
ORDER BY location_id
"""

df = client.query(query).to_dataframe()
print(df)
