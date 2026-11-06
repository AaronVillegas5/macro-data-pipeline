"""
tests/test_fixes.py — Tests covering MustFix and ShouldFix bug fixes and optimizations:
- Finding 1: jobs.fetch_weather.run accepts optional lat/lon arguments without TypeError
- Finding 2: jobs.fetch_retail.run handles errors without UnboundLocalError
- Finding 3 & 8: weather_service extracts precipitation, save_weather maps precipitation and supports batching
- Finding 4: agent_tools uses BigQuery parameterized queries
- Finding 5: insights/health/freshness handles naive and timezone-aware datetimes
- Finding 6: discord_notifier enforces request timeout and exception safety
- Finding 7: Airflow DAG has catchup=False
- Finding 9: SARIMAX engine caches optimal orders
- Finding 10: evaluator returns None for MAPE on zero-actuals and serializes cleanly
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure airflow mock is present if not installed
if "airflow" not in sys.modules:
    mock_airflow = MagicMock()
    sys.modules["airflow"] = mock_airflow
    sys.modules["airflow.operators"] = MagicMock()
    sys.modules["airflow.operators.bash"] = MagicMock()
    sys.modules["airflow.operators.python"] = MagicMock()

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from services.forecasting.evaluator import evaluate
from services.forecasting.sarimax_engine import fit_and_forecast, clear_order_cache, get_cached_orders
from utilities.discord_notifier import post_discord_alert

client = TestClient(app)


# ── Finding 1: Weather background job coordinates ─────────────────────────────


def test_fetch_weather_run_accepts_coordinates():
    """Verify jobs.fetch_weather.run accepts lat and lon arguments without TypeError."""
    import jobs.fetch_weather as fw

    with (
        patch.object(fw, "SessionLocal") as mock_session_cls,
        patch.object(fw, "get_snowflake_connection", return_value=None),
        patch.object(fw, "fetch_weather_for_location") as mock_fetch,
    ):
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loc = MagicMock(id=1, name="Test City", latitude=33.64, longitude=-117.60)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_loc

        # Calling with lat, lon must not raise TypeError:
        fw.run(lat=33.64, lon=-117.60)
        mock_fetch.assert_called_once()


def test_api_jobs_weather_triggers_successfully():
    """Verify POST /jobs/weather initiates without crashing."""
    response = client.post("/jobs/weather", json={"lat": 33.6405, "lon": -117.6026})
    assert response.status_code == 200
    assert response.json()["status"] == "weather job started"


# ── Finding 2: Census Retail UnboundLocalError ─────────────────────────────────


def test_fetch_retail_error_does_not_raise_unbound_local():
    """Verify that if save_retail fails, fetch_retail.run does not raise UnboundLocalError."""
    import jobs.fetch_retail as fr

    with (
        patch.object(fr, "fetch_retail_series", return_value=[{"dummy": 1}]),
        patch.object(fr, "save_retail", side_effect=RuntimeError("Database down")),
    ):
        # Must not raise UnboundLocalError:
        try:
            fr.run()
        except UnboundLocalError:
            pytest.fail("jobs.fetch_retail.run raised UnboundLocalError when save_retail failed")


# ── Finding 3 & 8: Weather precipitation & batch saving ────────────────────────


def test_weather_service_extracts_precipitation():
    """Verify fetch_weather extracts precipitation from hourly response."""
    from services.weather_service import fetch_weather

    mock_api_data = {
        "hourly": {
            "time": ["2026-08-01T00:00", "2026-08-01T01:00"],
            "temperature_2m": [22.5, 21.0],
            "windspeed_10m": [5.0, 4.5],
            "pressure_msl": [1013.2, 1013.0],
            "relative_humidity_2m": [60.0, 65.0],
            "precipitation": [1.2, 0.0],
        }
    }
    with patch("services.weather_service.get_weather", return_value=mock_api_data):
        rows = fetch_weather(33.64, -117.60)
        assert len(rows) == 2
        assert rows[0]["precipitation"] == 1.2
        assert rows[1]["precipitation"] == 0.0


def test_save_weather_batch_handles_lists_and_precipitation():
    """Verify save_weather accepts list of rows and includes precipitation."""
    import services.save_weather as sw

    test_rows = [
        {
            "location_id": 1,
            "temperature_c": 20.0,
            "wind_speed": 5.0,
            "pressure": 1012.0,
            "humidity": 50.0,
            "precipitation": 2.5,
            "observed_at": datetime.now(timezone.utc),
        }
    ]

    with (
        patch.object(sw, "SessionLocal") as mock_session_cls,
        patch("services.save_weather.bigquery.Client") as mock_bq_cls,
    ):
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_bq_client = MagicMock()
        mock_bq_cls.return_value = mock_bq_client
        mock_bq_client.insert_rows_json.return_value = []

        with patch.dict(os.environ, {"BIGQUERY_PROJECT_ID": "test-project"}):
            # Test batch write:
            sw.save_weather(test_rows)

        # Assert Postgres executed statement
        assert mock_db.execute.called
        # Assert BigQuery received the batch with precipitation
        assert mock_bq_client.insert_rows_json.called
        call_args = mock_bq_client.insert_rows_json.call_args[0]
        rows_sent = call_args[1]
        assert len(rows_sent) == 1
        assert rows_sent[0]["precipitation"] == 2.5


# ── Finding 4: BigQuery SQL Parameterization ──────────────────────────────────


def test_agent_tools_use_query_parameters():
    """Verify BigQuery tools generate parameterized queries rather than string formatting."""
    import services.agent_tools as at

    with patch.object(at, "get_bq_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.query.return_value = []

        # 1. query_macro_weather_mart
        at.query_macro_weather_mart("2024-01", "2024-06", "Irvine'; DROP TABLE users; --")
        call_args = mock_client.query.call_args
        query_sql = call_args[0][0]
        job_config = call_args[1].get("job_config")

        assert "@start_date" in query_sql
        assert "@end_date" in query_sql
        assert "@location_name" in query_sql
        assert "DROP TABLE" not in query_sql
        assert job_config is not None
        param_names = [p.name for p in job_config.query_parameters]
        assert "location_name" in param_names

        # 2. compare_city_climates
        at.compare_city_climates("CityA", "CityB", 2024)
        call_args2 = mock_client.query.call_args
        query_sql2 = call_args2[0][0]
        job_config2 = call_args2[1].get("job_config")
        assert "@year_prefix" in query_sql2
        assert "@cities" in query_sql2
        assert job_config2 is not None


# ── Finding 5: Freshness Timezone Handling ─────────────────────────────────────


def test_freshness_endpoint_supports_naive_and_aware_datetimes():
    """Verify health/freshness handles both naive and timezone-aware datetimes without TypeError."""
    from app.routers.insights import check_freshness

    mock_db = MagicMock()

    # Case A: Naive datetime
    naive_dt = datetime.now() - timedelta(hours=2)
    mock_db.execute.return_value.scalar.return_value = naive_dt
    res_naive = check_freshness(db=mock_db)
    assert res_naive["status"] == "HEALTHY"

    # Case B: Timezone-aware UTC datetime
    aware_dt = datetime.now(timezone.utc) - timedelta(hours=2)
    mock_db.execute.return_value.scalar.return_value = aware_dt
    res_aware = check_freshness(db=mock_db)
    assert res_aware["status"] == "HEALTHY"


# ── Finding 6: Discord webhook timeout and resilience ──────────────────────────


def test_post_discord_alert_timeout_and_error_handling():
    """Verify post_discord_alert specifies timeout=10 and catches network errors."""
    with (
        patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/test/test"}),
        patch("requests.post", side_effect=Exception("Connection timed out")) as mock_post,
    ):
        # Must not raise an exception:
        try:
            post_discord_alert("TestJob", "column_x", "Some error")
        except Exception:
            pytest.fail("post_discord_alert raised an uncaught exception on network failure")

        assert mock_post.called
        assert mock_post.call_args[1].get("timeout") == 10


# ── Finding 7: Airflow DAG catchup=False ────────────────────────────────────────


def test_airflow_dag_catchup_is_disabled():
    """Verify macro_weather_daily_pipeline has catchup=False in source."""
    dag_path = Path(__file__).resolve().parent.parent / "dags" / "macro_weather_dag.py"
    with open(dag_path, "r", encoding="utf-8") as f:
        source = f.read()
    assert "catchup=False" in source


# ── Finding 9: SARIMAX Order Caching ──────────────────────────────────────────


def test_sarimax_caching_speeds_up_subsequent_runs():
    """Verify optimal (order, seasonal_order) is cached and reused on repeated fits."""
    clear_order_cache()

    t = pd.date_range("2020-01-01", periods=36, freq="MS")
    series = pd.Series(np.linspace(10, 20, 36) + np.sin(np.arange(36)), index=t, name="test_metric")

    # First run: fits and populates cache
    res1 = fit_and_forecast(series, test_steps=6, use_cache=True)
    assert "test_metric" in get_cached_orders()

    # Second run: should reuse cached order instantly
    with patch("services.forecasting.sarimax_engine._aic_grid_search") as mock_grid:
        res2 = fit_and_forecast(series, test_steps=6, use_cache=True)
        # Grid search should NOT be called when cache hits
        mock_grid.assert_not_called()
        assert res2.model_order == res1.model_order
        assert res2.seasonal_order == res1.seasonal_order


# ── Finding 10: Evaluator MAPE None and JSON Serialization ────────────────────


def test_evaluator_returns_none_mape_when_actuals_are_zero():
    """Verify evaluator returns None instead of float('nan') when actuals are all 0."""
    actual = pd.Series([0.0, 0.0, 0.0], index=pd.date_range("2024-01-01", periods=3, freq="MS"))
    predicted = pd.Series([0.1, 0.2, 0.0], index=actual.index)

    metrics = evaluate(actual=actual, predicted=predicted)
    assert metrics.mape is None

    # Test serialization in Pydantic EvaluateResponse
    from app.routers.forecasting import MetricsPayload

    payload = MetricsPayload(rmse=metrics.rmse, mae=metrics.mae, mape=metrics.mape)
    json_data = payload.model_dump_json()
    assert '"mape":null' in json_data or '"mape": null' in json_data
