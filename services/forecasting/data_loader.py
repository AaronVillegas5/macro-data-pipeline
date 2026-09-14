"""
data_loader.py — Domain-isolated time series extraction from BigQuery.

Each domain (weather, retail, economic) uses a strictly separate query
strategy to prevent cross-domain feature leakage / spurious correlations.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import pandas as pd

PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "macro-data-pipeline-498302")
MART_TABLE = f"`{PROJECT_ID}.weather_data.fct_monthly_retail_macro`"
WEATHER_TABLE = f"`{PROJECT_ID}.weather_data.fct_monthly_macro_weather`"

# Allowed metrics per domain — enforced at load time
DOMAIN_METRICS: dict[str, list[str]] = {
    "weather": ["avg_monthly_temp_c", "total_monthly_precipitation_mm", "subzero_days"],
    "economic": ["cpi", "unemployment_rate", "gdp"],
    "retail": [
        "total_retail_sales_millions",
        "grocery_sales_millions",
        "ecommerce_sales_millions",
        "auto_sales_millions",
        "clothing_sales_millions",
    ],
}

_bq_client = None


def _get_bq_client():
    global _bq_client
    if _bq_client is None:
        from google.cloud import bigquery  # deferred — avoids crash without GCP creds
        _bq_client = bigquery.Client()
    return _bq_client


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_year_month_index(df: pd.DataFrame) -> pd.DataFrame:
    """Converts 'year_month' (YYYY-MM string) into a proper monthly DatetimeIndex."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["year_month"] + "-01", format="%Y-%m-%d")
    df = df.sort_values("date").set_index("date")
    df.index = df.index.to_period("M").to_timestamp("MS")
    df.index.freq = "MS"
    return df


def _train_test_split(series: pd.Series, test_months: int) -> tuple[pd.Series, pd.Series]:
    if len(series) <= test_months:
        raise ValueError(
            f"Series has {len(series)} observations but {test_months} test months were "
            "requested. Reduce test_months or provide more historical data."
        )
    return series.iloc[:-test_months], series.iloc[-test_months:]


# ── Domain-isolated query builders ────────────────────────────────────────────

def _load_weather_series(metric: str, location_name: str) -> pd.DataFrame:
    """Query a single city's monthly weather metric.

    Filters strictly on location_name to isolate local climate patterns.
    No retail or cross-domain columns are selected.
    """
    if not location_name:
        raise ValueError("location_name is required for domain='weather'.")
    query = f"""
        SELECT
            year_month,
            location_name,
            {metric}
        FROM {WEATHER_TABLE}
        WHERE location_name = @location_name
          AND year_month IS NOT NULL
          AND {metric} IS NOT NULL
        ORDER BY year_month ASC
    """
    from google.cloud import bigquery
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("location_name", "STRING", location_name)
        ]
    )
    return _get_bq_client().query(query, job_config=job_config).to_dataframe()


def _load_economic_series(metric: str) -> pd.DataFrame:
    """Query distinct national economic indicator rows by year_month.

    SELECT DISTINCT prevents duplication from the city-level mart join.
    No weather or retail columns are selected.
    """
    query = f"""
        SELECT DISTINCT
            year_month,
            {metric}
        FROM {MART_TABLE}
        WHERE year_month IS NOT NULL
          AND {metric} IS NOT NULL
        ORDER BY year_month ASC
    """
    return _get_bq_client().query(query).to_dataframe()


def _load_retail_series(metric: str) -> pd.DataFrame:
    """Query distinct national retail sales rows by year_month.

    Uses SELECT DISTINCT because fct_monthly_retail_macro joins city-level
    weather rows, duplicating retail totals across every city.
    Excludes all weather/location columns to prevent spurious cross-correlation
    between local city weather and national retail aggregates.
    """
    query = f"""
        SELECT DISTINCT
            year_month,
            {metric}
        FROM {MART_TABLE}
        WHERE year_month IS NOT NULL
          AND {metric} IS NOT NULL
        ORDER BY year_month ASC
    """
    return _get_bq_client().query(query).to_dataframe()


# ── Result container ───────────────────────────────────────────────────────────

@dataclass
class SeriesResult:
    """Prepared time-series ready for SARIMAX modelling."""
    domain: str
    metric: str
    location_name: Optional[str]
    train: pd.Series
    test: pd.Series


# ── Public interface ───────────────────────────────────────────────────────────

def load_series(
    domain: str,
    metric: str,
    location_name: Optional[str] = None,
    test_months: int = 12,
) -> SeriesResult:
    """Load and split a monthly time series for SARIMAX modelling.

    Args:
        domain:        One of 'weather', 'economic', 'retail'.
        metric:        Column to model (validated against DOMAIN_METRICS).
        location_name: Required when domain='weather'. Ignored otherwise.
        test_months:   Number of trailing months held out for evaluation.

    Returns:
        SeriesResult with (train, test) pd.Series at MonthStart frequency.
    """
    allowed = DOMAIN_METRICS.get(domain)
    if allowed is None:
        raise ValueError(f"Unknown domain '{domain}'. Choose from: {list(DOMAIN_METRICS)}")
    if metric not in allowed:
        raise ValueError(
            f"Metric '{metric}' is not valid for domain='{domain}'. Allowed: {allowed}"
        )

    if domain == "weather":
        df = _load_weather_series(metric, location_name)
    elif domain == "economic":
        df = _load_economic_series(metric)
    else:  # retail
        df = _load_retail_series(metric)

    df = _parse_year_month_index(df)
    series = df[metric].astype(float).dropna()

    if series.empty:
        raise ValueError(f"No data returned for domain='{domain}', metric='{metric}'.")

    train, test = _train_test_split(series, test_months)
    return SeriesResult(
        domain=domain,
        metric=metric,
        location_name=location_name,
        train=train,
        test=test,
    )


def make_synthetic_series(
    domain: str = "retail",
    metric: str = "total_retail_sales_millions",
    location_name: Optional[str] = None,
    n_obs: int = 72,
    test_months: int = 12,
    seed: int = 42,
) -> SeriesResult:
    """Generate a synthetic monthly time-series for offline unit testing.

    Produces trend + annual seasonality + Gaussian noise without GCP calls.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    t = pd.date_range(start="2018-01-01", periods=n_obs, freq="MS")
    seasonal = 10 * np.sin(2 * np.pi * t.month / 12)
    trend = 0.5 * np.arange(n_obs)
    noise = rng.normal(0, 3, n_obs)
    values = (450 + trend + seasonal + noise).astype(float)
    series = pd.Series(values, index=t, name=metric)
    train, test = _train_test_split(series, test_months)
    return SeriesResult(domain=domain, metric=metric, location_name=location_name, train=train, test=test)

