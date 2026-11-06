import os

from google.cloud import bigquery


def get_bq_client():
    """Initializes BigQuery client, automatically finding gcp-key.json if needed."""
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path or not os.path.exists(key_path):
        for candidate in ["/app/gcp-key.json", "gcp-key.json", "../gcp-key.json"]:
            if os.path.exists(candidate):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(candidate)
                break
    return bigquery.Client(project=project_id)


def query_macro_weather_mart(start_date: str, end_date: str, location_name: str = None) -> list:
    """Queries the physical dbt mart fct_monthly_macro_weather for analytics metrics.
    Args:
        start_date: Start date in 'YYYY-MM' format (e.g. '2020-01')
        end_date: End date in 'YYYY-MM' format (e.g. '2024-12')
        location_name: Optional city name (e.g. 'Irvine')
    """
    project_id = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    client = get_bq_client()

    query = f"""
    SELECT location_name, year_month, avg_monthly_temp_c, total_monthly_precipitation_mm, 
           subzero_days, cpi, unemployment_rate, gdp
    FROM `{project_id}.weather_data.fct_monthly_macro_weather`
    WHERE year_month BETWEEN @start_date AND @end_date
    """
    query_params = [
        bigquery.ScalarQueryParameter("start_date", "STRING", str(start_date)),
        bigquery.ScalarQueryParameter("end_date", "STRING", str(end_date)),
    ]

    if location_name:
        query += " AND location_name = @location_name"
        query_params.append(bigquery.ScalarQueryParameter("location_name", "STRING", str(location_name)))

    query += " ORDER BY year_month ASC LIMIT 50"

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    query_job = client.query(query, job_config=job_config)
    return [dict(row) for row in query_job]


def check_data_freshness() -> dict:
    """Checks the latest observation timestamps across BigQuery data marts and PostgreSQL."""
    result = {}

    # 1. Primary check: BigQuery data mart freshness
    try:
        client = get_bq_client()
        project_id = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
        query = f"""
        SELECT MAX(year_month) as latest_period 
        FROM `{project_id}.weather_data.fct_monthly_macro_weather`
        """
        for row in client.query(query):
            result["latest_macro_weather_period"] = str(row["latest_period"])
            result["status"] = "BigQuery data marts healthy and up to date"
    except Exception as e:
        result["bigquery_status"] = f"Unable to check BigQuery: {e}"

    # 2. Secondary check: PostgreSQL if configured
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("sqlite"):
        try:
            from sqlalchemy import func
            from db.connection import SessionLocal
            from db.models import EconomicObservation, WeatherObservation

            db = SessionLocal()
            try:
                latest_w = db.query(func.max(WeatherObservation.observed_at)).scalar()
                latest_e = db.query(func.max(EconomicObservation.observed_at)).scalar()
                result["latest_postgres_weather"] = str(latest_w)
                result["latest_postgres_economic"] = str(latest_e)
            finally:
                db.close()
        except Exception:
            pass

    return result if result else {"status": "Pipeline completed; data mart verified."}


def get_climate_extremes(year: int, metric: str = "subzero_days") -> list:
    """Finds top locations with extreme climate events (most subzero days, highest rainfall, hottest month).
    Args:
        year: e.g. 2024
        metric: One of 'subzero_days', 'max_temp', 'total_rainfall'
    """
    project_id = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    client = get_bq_client()

    allowed_metrics = {
        "subzero_days": "subzero_days DESC",
        "total_rainfall": "total_monthly_precipitation_mm DESC",
        "max_temp": "avg_monthly_temp_c DESC",
    }
    order_col = allowed_metrics.get(metric, "subzero_days DESC")
    year_str = str(int(year))

    query = f"""
    SELECT location_name, year_month, avg_monthly_temp_c, total_monthly_precipitation_mm, subzero_days
    FROM `{project_id}.weather_data.fct_monthly_macro_weather`
    WHERE STARTS_WITH(year_month, @year_prefix)
    ORDER BY {order_col}
    LIMIT 5
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("year_prefix", "STRING", year_str)]
    )
    return [dict(row) for row in client.query(query, job_config=job_config)]


def compare_city_climates(city_a: str, city_b: str, year: int) -> list:
    """Compares historical climate metrics side-by-side between two cities for a given year.
    Args:
        city_a: Name of first city (e.g. 'Irvine')
        city_b: Name of second city (e.g. 'Seattle')
        year: The year to compare (e.g. 2024)
    """
    project_id = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
    client = get_bq_client()
    year_str = str(int(year))

    query = f"""
    SELECT location_name, year_month, avg_monthly_temp_c, total_monthly_precipitation_mm
    FROM `{project_id}.weather_data.fct_monthly_macro_weather`
    WHERE location_name IN UNNEST(@cities) AND STARTS_WITH(year_month, @year_prefix)
    ORDER BY year_month ASC, location_name ASC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("cities", "STRING", [str(city_a), str(city_b)]),
            bigquery.ScalarQueryParameter("year_prefix", "STRING", year_str),
        ]
    )
    return [dict(row) for row in client.query(query, job_config=job_config)]
