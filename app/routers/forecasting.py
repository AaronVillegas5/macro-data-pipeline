"""
app/routers/forecasting.py — SARIMAX forecasting and evaluation API endpoints.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, field_validator, model_validator

from services.forecasting.data_loader import DOMAIN_METRICS, load_series
from services.forecasting.sarimax_engine import fit_and_forecast
from services.forecasting.evaluator import evaluate
from services.forecasting.visualizer import build_evaluation_chart

router = APIRouter(prefix="/forecast", tags=["Forecasting"])


# ── Request/Response Models ───────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    domain: str
    metric: str
    location_name: Optional[str] = None
    test_months: int = 12
    forecast_months: int = 12

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        if v not in DOMAIN_METRICS:
            raise ValueError(f"domain must be one of {list(DOMAIN_METRICS)}")
        return v

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v: str, info: Any) -> str:
        # Full validation happens in data_loader.load_series; lightweight check here
        return v

    @model_validator(mode="after")
    def require_location_for_weather(self) -> "EvaluateRequest":
        if self.domain == "weather" and not self.location_name:
            raise ValueError("location_name is required when domain='weather'.")
        return self

    @field_validator("test_months", "forecast_months")
    @classmethod
    def positive_months(cls, v: int) -> int:
        if v < 1:
            raise ValueError("test_months and forecast_months must be >= 1.")
        return v


class PredictRequest(BaseModel):
    domain: str
    metric: str
    location_name: Optional[str] = None
    test_months: int = 12
    forecast_months: int = 12

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        if v not in DOMAIN_METRICS:
            raise ValueError(f"domain must be one of {list(DOMAIN_METRICS)}")
        return v

    @model_validator(mode="after")
    def require_location_for_weather(self) -> "PredictRequest":
        if self.domain == "weather" and not self.location_name:
            raise ValueError("location_name is required when domain='weather'.")
        return self


class MetricsPayload(BaseModel):
    rmse: float
    mae: float
    mape: float


class EvaluateResponse(BaseModel):
    domain: str
    metric: str
    location_name: Optional[str]
    model_order: list[int]
    seasonal_order: list[int]
    aic: float
    test_months: int
    metrics: MetricsPayload
    actual: dict[str, float]       # {ISO date string: value}
    predicted: dict[str, float]
    conf_int_lower: dict[str, float]
    conf_int_upper: dict[str, float]
    chart_png_base64: str


class PredictResponse(BaseModel):
    domain: str
    metric: str
    location_name: Optional[str]
    model_order: list[int]
    seasonal_order: list[int]
    aic: float
    forecast: dict[str, float]
    conf_int_lower: dict[str, float]
    conf_int_upper: dict[str, float]


# ── Helper ────────────────────────────────────────────────────────────────────

def _series_to_dict(s) -> dict[str, float]:
    """Convert a pd.Series with DatetimeIndex to {ISO date string: value}."""
    return {str(k.date()): round(float(v), 4) for k, v in s.items()}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/arima/evaluate", response_model=EvaluateResponse)
def evaluate_forecast(payload: EvaluateRequest):
    """Run SARIMAX backtest evaluation against the holdout period.

    Returns error metrics (RMSE, MAE, MAPE), actual vs. predicted trajectories,
    95% confidence intervals, and a base64-encoded PNG chart.
    """
    try:
        series = load_series(
            domain=payload.domain,
            metric=payload.metric,
            location_name=payload.location_name,
            test_months=payload.test_months,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data loading error: {e}")

    try:
        forecast = fit_and_forecast(
            train=series.train,
            test_steps=payload.test_months,
            forecast_steps=0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model fitting error: {e}")

    try:
        metrics = evaluate(actual=series.test, predicted=forecast.predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation error: {e}")

    try:
        _, chart_b64 = build_evaluation_chart(
            train=series.train,
            actual=series.test,
            predicted=forecast.predictions,
            conf_int=forecast.conf_int,
            metric=payload.metric,
            domain=payload.domain,
            location_name=payload.location_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation error: {e}")

    return EvaluateResponse(
        domain=payload.domain,
        metric=payload.metric,
        location_name=payload.location_name,
        model_order=list(forecast.model_order),
        seasonal_order=list(forecast.seasonal_order),
        aic=round(forecast.aic, 4),
        test_months=payload.test_months,
        metrics=MetricsPayload(
            rmse=metrics.rmse,
            mae=metrics.mae,
            mape=metrics.mape,
        ),
        actual=_series_to_dict(series.test),
        predicted=_series_to_dict(forecast.predictions),
        conf_int_lower=_series_to_dict(forecast.conf_int["lower"]),
        conf_int_upper=_series_to_dict(forecast.conf_int["upper"]),
        chart_png_base64=chart_b64,
    )


@router.get("/arima/evaluate/plot")
def evaluate_forecast_plot(
    domain: str = Query(..., description="Domain: weather, economic, retail"),
    metric: str = Query(..., description="Target metric column"),
    location_name: Optional[str] = Query(None, description="City name (required for weather)"),
    test_months: int = Query(12, ge=1),
):
    """Stream the evaluation trajectory chart directly as image/png.

    Suitable for embedding in a browser or Slack/Discord image link.
    """
    if domain == "weather" and not location_name:
        raise HTTPException(status_code=422, detail="location_name is required for domain='weather'.")

    try:
        series = load_series(
            domain=domain,
            metric=metric,
            location_name=location_name,
            test_months=test_months,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data loading error: {e}")

    try:
        forecast = fit_and_forecast(train=series.train, test_steps=test_months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model fitting error: {e}")

    try:
        png_bytes, _ = build_evaluation_chart(
            train=series.train,
            actual=series.test,
            predicted=forecast.predictions,
            conf_int=forecast.conf_int,
            metric=metric,
            domain=domain,
            location_name=location_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation error: {e}")

    return Response(content=png_bytes, media_type="image/png")


@router.post("/arima/predict", response_model=PredictResponse)
def predict_future(payload: PredictRequest):
    """Generate a forward-looking SARIMAX forecast beyond the current data horizon.

    Returns predicted values and 95% confidence intervals for forecast_months ahead.
    """
    try:
        series = load_series(
            domain=payload.domain,
            metric=payload.metric,
            location_name=payload.location_name,
            test_months=payload.test_months,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data loading error: {e}")

    # Train on ALL available data (train + test) for maximum future accuracy
    import pandas as pd
    full_series = pd.concat([series.train, series.test])

    try:
        forecast = fit_and_forecast(
            train=full_series,
            test_steps=0,
            forecast_steps=payload.forecast_months,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model fitting error: {e}")

    if forecast.future_forecast is None:
        raise HTTPException(status_code=500, detail="No future forecast was generated.")

    return PredictResponse(
        domain=payload.domain,
        metric=payload.metric,
        location_name=payload.location_name,
        model_order=list(forecast.model_order),
        seasonal_order=list(forecast.seasonal_order),
        aic=round(forecast.aic, 4),
        forecast=_series_to_dict(forecast.future_forecast),
        conf_int_lower=_series_to_dict(forecast.future_conf_int["lower"]),
        conf_int_upper=_series_to_dict(forecast.future_conf_int["upper"]),
    )

