"""
visualizer.py — Trajectory plot: actual vs. predicted with confidence interval.

IMPORTANT: matplotlib.use("Agg") MUST be called before importing pyplot.
This is required for headless operation in Docker, Linux CI, and FastAPI worker
threads where no display server is available.
"""

from __future__ import annotations

import base64
import io
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # Must be set before importing pyplot to prevent headless server crashes
import matplotlib.pyplot as plt
import pandas as pd


def _build_figure(
    actual: pd.Series,
    predicted: pd.Series,
    conf_int: pd.DataFrame,
    train: pd.Series,
    metric: str,
    domain: str,
    location_name: Optional[str] = None,
    future_forecast: Optional[pd.Series] = None,
    future_conf_int: Optional[pd.DataFrame] = None,
) -> plt.Figure:
    """Construct a Matplotlib figure comparing actual vs predicted trajectories."""
    title_parts = [f"SARIMAX Forecast — {domain.capitalize()}: {metric}"]
    if location_name:
        title_parts.append(f"({location_name})")

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    # Historical training series
    ax.plot(
        train.index,
        train.values,
        color="#8ab4f8",
        linewidth=1.4,
        label="Historical (train)",
        alpha=0.85,
    )

    # Actual test values
    ax.plot(
        actual.index,
        actual.values,
        color="#34a853",
        linewidth=2,
        marker="o",
        markersize=4,
        label="Actual (test)",
    )

    # Predicted test values
    ax.plot(
        predicted.index,
        predicted.values,
        color="#fbbc04",
        linewidth=2,
        linestyle="--",
        marker="s",
        markersize=4,
        label="Predicted (SARIMAX)",
    )

    # 95% confidence interval shading
    ax.fill_between(
        conf_int.index,
        conf_int["lower"],
        conf_int["upper"],
        color="#fbbc04",
        alpha=0.15,
        label="95% CI",
    )

    # Optional future forecast
    if future_forecast is not None and not future_forecast.empty:
        ax.plot(
            future_forecast.index,
            future_forecast.values,
            color="#ea4335",
            linewidth=1.8,
            linestyle=":",
            label="Future Forecast",
        )
        if future_conf_int is not None:
            ax.fill_between(
                future_conf_int.index,
                future_conf_int["lower"],
                future_conf_int["upper"],
                color="#ea4335",
                alpha=0.12,
            )

    # Vertical divider between train/test
    if not actual.empty:
        ax.axvline(actual.index[0], color="#5f6368", linestyle=":", linewidth=1, alpha=0.7)

    # Styling
    ax.set_title(" ".join(title_parts), color="white", fontsize=13, pad=12)
    ax.set_xlabel("Date", color="#9aa0a6", fontsize=10)
    ax.set_ylabel(metric, color="#9aa0a6", fontsize=10)
    ax.tick_params(colors="#9aa0a6", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#3c4043")
    legend = ax.legend(facecolor="#1c1e26", edgecolor="#3c4043", labelcolor="white", fontsize=9)
    fig.tight_layout()
    return fig


def render_to_bytes(fig: plt.Figure, dpi: int = 150) -> bytes:
    """Render a Matplotlib figure to PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def render_to_base64(fig: plt.Figure, dpi: int = 150) -> str:
    """Render a Matplotlib figure to a base64-encoded PNG string."""
    return base64.b64encode(render_to_bytes(fig, dpi=dpi)).decode("utf-8")


def build_evaluation_chart(
    train: pd.Series,
    actual: pd.Series,
    predicted: pd.Series,
    conf_int: pd.DataFrame,
    metric: str,
    domain: str,
    location_name: Optional[str] = None,
    future_forecast: Optional[pd.Series] = None,
    future_conf_int: Optional[pd.DataFrame] = None,
) -> tuple[bytes, str]:
    """Build and return evaluation chart as (png_bytes, base64_string).

    Args:
        train:          Training portion of the time-series.
        actual:         Actual held-out test values.
        predicted:      SARIMAX point forecast for the test period.
        conf_int:       DataFrame with 'lower' and 'upper' columns.
        metric:         Column name being plotted (used for y-axis label).
        domain:         Domain name for chart title.
        location_name:  Optional city for weather charts.
        future_forecast: Optional forward-looking forecast series.
        future_conf_int: Optional confidence interval for future forecast.

    Returns:
        (png_bytes, base64_png_string)
    """
    fig = _build_figure(
        actual=actual,
        predicted=predicted,
        conf_int=conf_int,
        train=train,
        metric=metric,
        domain=domain,
        location_name=location_name,
        future_forecast=future_forecast,
        future_conf_int=future_conf_int,
    )
    png_bytes = render_to_bytes(fig)
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return png_bytes, b64
