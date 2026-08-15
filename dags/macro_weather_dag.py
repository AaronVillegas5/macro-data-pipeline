from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
# pyrefly: ignore [missing-import]
from airflow.operators.bash import BashOperator

# Default arguments applied to all tasks
default_args = {
    "owner": "Aaron Villegas",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def run_weather_ingestion(**kwargs):
    from jobs.fetch_weather import run as fetch_weather_run
    # Fetches latest weather for all locations in the PostgreSQL database
    fetch_weather_run()

def run_economic_ingestion(**kwargs):
    from jobs.fetch_economic import run as fetch_economic_run, FRED_SERIES
    for series_id, name in FRED_SERIES.items():
        fetch_economic_run(series_id, name)

with DAG(
    dag_id="macro_weather_daily_pipeline",
    default_args=default_args,
    description="Daily ingestion of FRED & Weather APIs followed by dbt BigQuery transformations",
    schedule_interval="0 6 * * *",  # Runs daily at 06:00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["macro", "weather", "dbt", "production"],
) as dag:

    ingest_weather = PythonOperator(
        task_id="ingest_weather_observations",
        python_callable=run_weather_ingestion,
    )

    ingest_economic = PythonOperator(
        task_id="ingest_fred_economic_data",
        python_callable=run_economic_ingestion,
    )

    # Trigger dbt run for BigQuery models
    dbt_run = BashOperator(
        task_id="dbt_run_transformations",
        bash_command="cd /opt/airflow/project_root/dbt && dbt run --profiles-dir .",
    )

    # Trigger dbt tests to validate data quality
    dbt_test = BashOperator(
        task_id="dbt_test_quality_checks",
        bash_command="cd /opt/airflow/project_root/dbt && dbt test --profiles-dir .",
    )

    # Set DAG Dependencies
    [ingest_weather, ingest_economic] >> dbt_run >> dbt_test
