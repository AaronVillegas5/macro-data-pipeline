"""
sarimax_engine.py — SARIMAX model fitting, order search, and forecasting.
"""
from __future__ import annotations

import itertools
import warnings
from dataclasses import dataclass
from typing import Optional

import pandas as pd

# Suppress verbose statsmodels convergence output in production logs
warnings.filterwarnings("ignore", module="statsmodels")


@dataclass
class ForecastResult:
    """Output of a SARIMAX fit and forecast."""
    model_order: tuple          # (p, d, q)
    seasonal_order: tuple       # (P, D, Q, s)
    aic: float
    predictions: pd.Series     # in-sample test period point forecast
    conf_int: pd.DataFrame      # columns: lower, upper (95% CI)
    future_forecast: Optional[pd.Series] = None
    future_conf_int: Optional[pd.DataFrame] = None


def _try_fit(train: pd.Series, order: tuple, seasonal_order: tuple) -> Optional[object]:
    """Attempt to fit a SARIMAX model, returning None on any failure."""
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        model = SARIMAX(
            train,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,   # prevents LinAlg crashes on non-stationary series
            enforce_invertibility=False,  # prevents LinAlg crashes on complex seasonal MA
        )
        return model.fit(disp=False, maxiter=200)
    except Exception:
        return None


def _aic_grid_search(
    train: pd.Series,
    p_values: tuple[int, ...] = (0, 1, 2),
    d_values: tuple[int, ...] = (0, 1),
    q_values: tuple[int, ...] = (0, 1, 2),
    P_values: tuple[int, ...] = (0, 1),
    D_values: tuple[int, ...] = (0, 1),
    Q_values: tuple[int, ...] = (0, 1),
    s: int = 12,
) -> tuple[object, tuple, tuple, float]:
    """Lightweight grid search over (p,d,q)(P,D,Q)_s minimising AIC.

    Returns (best_result, best_order, best_seasonal_order, best_aic).
    """
    best_result = None
    best_order = (1, 1, 1)
    best_seasonal_order = (1, 1, 1, s)
    best_aic = float("inf")

    for order in itertools.product(p_values, d_values, q_values):
        for seasonal_order_pdq in itertools.product(P_values, D_values, Q_values):
            seasonal_order = (*seasonal_order_pdq, s)
            result = _try_fit(train, order, seasonal_order)
            if result is not None and result.aic < best_aic:
                best_aic = result.aic
                best_result = result
                best_order = order
                best_seasonal_order = seasonal_order

    if best_result is None:
        # Last-resort fallback: simple ARIMA(1,1,1)
        best_order = (1, 1, 1)
        best_seasonal_order = (0, 0, 0, 0)
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        best_result = SARIMAX(
            train,
            order=best_order,
            seasonal_order=best_seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False, maxiter=200)
        best_aic = best_result.aic

    return best_result, best_order, best_seasonal_order, best_aic


def fit_and_forecast(
    train: pd.Series,
    test_steps: int,
    forecast_steps: int = 0,
    seasonal_period: int = 12,
) -> ForecastResult:
    """Fit the best SARIMAX model and generate predictions.

    Args:
        train:           Training series with MonthStart DatetimeIndex.
        test_steps:      Number of steps to forecast into the holdout period.
        forecast_steps:  Additional future steps beyond the test horizon.
        seasonal_period: Seasonal lag (12 for monthly data).

    Returns:
        ForecastResult with point forecasts and 95% confidence intervals.
    """
    result, order, seasonal_order, aic = _aic_grid_search(train, s=seasonal_period)

    # In-sample test forecast (covers the holdout period)
    forecast_obj = result.get_forecast(steps=test_steps)
    pred_mean = forecast_obj.predicted_mean
    pred_ci = forecast_obj.conf_int(alpha=0.05)
    pred_ci.columns = ["lower", "upper"]

    # Optional future forecast beyond test horizon
    future_mean = None
    future_ci = None
    if forecast_steps > 0:
        total_steps = test_steps + forecast_steps
        full_forecast = result.get_forecast(steps=total_steps)
        future_mean = full_forecast.predicted_mean.iloc[test_steps:]
        full_ci = full_forecast.conf_int(alpha=0.05)
        full_ci.columns = ["lower", "upper"]
        future_ci = full_ci.iloc[test_steps:]

    return ForecastResult(
        model_order=order,
        seasonal_order=seasonal_order,
        aic=aic,
        predictions=pred_mean,
        conf_int=pred_ci,
        future_forecast=future_mean,
        future_conf_int=future_ci,
    )

