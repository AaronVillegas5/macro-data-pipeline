import os
import sys
from datetime import datetime, timedelta

import requests

# Ensure project root is on sys.path for Airflow workers
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# pyrefly: ignore [missing-import]
from airflow import DAG

# pyrefly: ignore [missing-import]
from airflow.operators.bash import BashOperator

# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator


def send_discord_alert(context):
    webhook_url = "https://discord.com/api/webhooks/1538356817845948418/EC4I2UfYsZ-5TxOoi2RmmFKQ9ysMR_OCZzqWWQInTlN0KadfJwSB66PqioIwZMLmPHKK"
    task_instance = context.get("task_instance")
    task_id = task_instance.task_id
    execution_date = context.get("execution_date")

    payload = {
        "content": f"🚨 **Airflow Pipeline Failure!** 🚨\n**Task:** `{task_id}` failed on `{execution_date}`. Check the Airflow logs immediately."
    }
    requests.post(webhook_url, json=payload)


# Default arguments applied to all tasks
default_args = {
    "owner": "Aaron Villegas",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": send_discord_alert,
}


def run_weather_ingestion(**kwargs):
    from jobs.fetch_weather import run as fetch_weather_run

    # Fetches latest weather for all locations in the PostgreSQL database
    fetch_weather_run()


def run_economic_ingestion(**kwargs):
    from jobs.fetch_economic import run as fetch_economic_run

    # Fetches latest macroeconomic series from FRED API
    fetch_economic_run()


def run_retail_ingestion(**kwargs):
    from jobs.fetch_retail import run as fetch_retail_run

    # Fetches latest retail sales from U.S. Census API
    fetch_retail_run()


def run_daily_ai_briefing(**kwargs):
    from utilities.logger import logger

    try:
        from services.ai_agent import generate_daily_executive_briefing

        briefing = generate_daily_executive_briefing()
        logger.info(f"AI Executive Briefing generated successfully:\n{briefing}")
    except Exception as e:
        logger.warning(f"AI Briefing skipped or encountered an error: {e}")


with DAG(
    dag_id="macro_weather_daily_pipeline",
    default_args=default_args,
    description="Daily ingestion of FRED & Weather APIs followed by dbt BigQuery transformations",
    schedule_interval="0 6 * * *",  # Runs daily at 06:00 UTC
    start_date=datetime(2026, 8, 15),
    catchup=True,
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

    ingest_retail = PythonOperator(
        task_id="ingest_census_retail_data",
        python_callable=run_retail_ingestion,
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

    generate_briefing = PythonOperator(
        task_id="generate_ai_executive_briefing", python_callable=run_daily_ai_briefing
    )

    # Set DAG Dependencies, ingestion runs first, must be successful before dbt run, dbt test, and AI briefing occur
    (
        [ingest_weather, ingest_economic, ingest_retail]
        >> dbt_run
        >> dbt_test
        >> generate_briefing
    )
