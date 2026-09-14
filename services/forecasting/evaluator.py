"""
evaluator.py — Forecast accuracy metrics: RMSE, MAE, MAPE.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class EvaluationMetrics:
    """Error metrics computed between actual and predicted trajectories."""

    rmse: float  # Root Mean Squared Error — penalises large deviations
    mae: float  # Mean Absolute Error — average absolute deviation in original units
    mape: float  # Mean Absolute Percentage Error — scale-free %; None if actuals contain zeros


def evaluate(actual: pd.Series, predicted: pd.Series) -> EvaluationMetrics:
    """Compute RMSE, MAE, and MAPE between actual and predicted trajectories.

    Args:
        actual:    Held-out test values (pd.Series).
        predicted: Model forecast values aligned to the same index.

    Returns:
        EvaluationMetrics with float values rounded to 4 decimal places.
    """
    # Align on common index in case of timestamp offset mismatches
    actual, predicted = actual.align(predicted, join="inner")

    if actual.empty:
        raise ValueError("Cannot evaluate — actual and predicted series have no overlapping index.")

    errors = actual.values - predicted.values
    abs_errors = np.abs(errors)

    rmse = float(np.sqrt(np.mean(errors**2)))
    mae = float(np.mean(abs_errors))

    # MAPE: guard against division by zero
    nonzero_mask = actual.values != 0
    if nonzero_mask.sum() == 0:
        mape = float("nan")
    else:
        mape = float(np.mean(abs_errors[nonzero_mask] / np.abs(actual.values[nonzero_mask])) * 100)

    return EvaluationMetrics(
        rmse=round(rmse, 4),
        mae=round(mae, 4),
        mape=round(mape, 4),
    )
