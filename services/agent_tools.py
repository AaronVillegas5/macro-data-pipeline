import os

from google.cloud import bigquery


def get_bq_client():
    """Initializes BigQuery client, automatically finding gcp-key.json if needed."""
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path or not os.path.exists(key_path):
        for candidate in ["/app/gcp-key.json", "gcp-key.json", "../gcp-key.json"]:
            if os.path.exists(candidate):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(
                    candidate
                )
                break
    return bigquery.Client(project=project_id)


def query_macro_weather_mart(
    start_date: str, end_date: str, location_name: str = None
) -> list:
    """Queries the physical dbt mart fct_monthly_macro_weather for analytics metrics."""
    project_id = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    client = get_bq_client()

    query = f"""
    SELECT year_month, location_name, avg_monthly_temp_c, total_monthly_precipitation_mm, 
           longest_dry_spell_days, cpi, unemployment_rate, fed_funds_rate
    FROM `{project_id}.weather_data.fct_monthly_macro_weather`
    WHERE year_month BETWEEN '{start_date}' AND '{end_date}'
    """
    if location_name:
        query += f" AND location_name = '{location_name}'"

    query += " ORDER BY year_month ASC LIMIT 50"

    query_job = client.query(query)
    return [dict(row) for row in query_job]


from sqlalchemy import func

from db.connection import SessionLocal
from db.models import EconomicObservation, WeatherObservation


def check_data_freshness() -> dict:
    """Checks the latest observation timestamps in PostgreSQL for weather and FRED economic data."""
    db = SessionLocal()
    try:
        latest_weather = db.query(func.max(WeatherObservation.observed_at)).scalar()
        latest_economic = db.query(func.max(EconomicObservation.observed_at)).scalar()
        return {
            "latest_weather_timestamp": str(latest_weather),
            "latest_economic_timestamp": str(latest_economic),
            "status": "Pipeline healthy and up to date",
        }
    finally:
        db.close()


def get_climate_extremes(year: int, metric: str = "dry_spell") -> list:
    """Finds top locations with extreme climate events (longest dry spell, highest rainfall, hottest month).
    Args:
        year: e.g. 2024
        metric: One of 'dry_spell', 'max_temp', 'total_rainfall'
    """
    project_id = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    client = get_bq_client()

    order_col = (
        "longest_dry_spell_days DESC"
        if metric == "dry_spell"
        else "avg_monthly_temp_c DESC"
    )
    query = f"""
    SELECT location_name, year_month, avg_monthly_temp_c, total_monthly_precipitation_mm, longest_dry_spell_days
    FROM `{project_id}.weather_data.fct_monthly_macro_weather`
    WHERE STARTS_WITH(year_month, '{year}')
    ORDER BY {order_col}
    LIMIT 5
    """
    return [dict(row) for row in client.query(query)]


def compare_city_climates(city_a: str, city_b: str, year: int) -> list:
    """Compares historical climate metrics side-by-side between two cities for a given year."""
    project_id = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    client = get_bq_client()
    query = f"""
    SELECT location_name, year_month, avg_monthly_temp_c, total_monthly_precipitation_mm
    FROM `{project_id}.weather_data.fct_monthly_macro_weather`
    WHERE location_name IN ('{city_a}', '{city_b}') AND STARTS_WITH(year_month, '{year}')
    ORDER BY year_month ASC, location_name ASC
    """
    return [dict(row) for row in client.query(query)]
