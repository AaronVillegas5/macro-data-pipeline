from google.cloud import bigquery

client = bigquery.Client.from_service_account_json("gcp-key.json")
query = (
    "SELECT * FROM `macro-data-pipeline-498302.dbt_dev.fct_location_climate_summary`"
)

df = client.query(query).to_dataframe()
print(df.head(10))
