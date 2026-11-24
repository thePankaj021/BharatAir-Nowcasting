"""Transparent persistence baselines for chronological time-series evaluation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def evaluate_persistence_baselines(
    frame: pd.DataFrame,
    sensor_id: int,
    horizons_hours: tuple[int, ...] = (6, 24),
    train_fraction: float = 0.8,
    minimum_holdout_rows: int = 5,
) -> list[dict[str, Any]]:
    """Evaluate a persistence baseline using exact time lags and a chronological holdout.

    For each horizon h, the prediction for time t is the observed value at t-h.
    Rows without an exact h-hour lag are excluded rather than interpolated.
    The last chronological fraction is reserved for evaluation.
    """
    required = {"datetime_from_utc", "value"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    if not 0.5 <= train_fraction < 1:
        raise ValueError("train_fraction must be at least 0.5 and less than 1.")

    timestamps = pd.to_datetime(frame["datetime_from_utc"], utc=True, errors="coerce")
    values = pd.to_numeric(frame["value"], errors="coerce")
    series = pd.Series(values.to_numpy(), index=timestamps)
    series = series[series.index.notna()].dropna()
    series = series[~series.index.duplicated(keep="last")].sort_index()

    unit = (
        str(frame["unit"].dropna().iloc[0])
        if "unit" in frame.columns and not frame["unit"].dropna().empty
        else None
    )

    results: list[dict[str, Any]] = []
    for horizon in horizons_hours:
        if horizon <= 0:
            raise ValueError("Forecast horizons must be positive integers.")

        target_times = series.index
        lag_times = target_times - pd.Timedelta(hours=horizon)
        aligned = pd.DataFrame(
            {
                "actual": series.to_numpy(),
                "prediction": series.reindex(lag_times).to_numpy(),
            },
            index=target_times,
        ).dropna()

        split_at = int(len(aligned) * train_fraction)
        holdout = aligned.iloc[split_at:]
        result: dict[str, Any] = {
            "sensor_id": sensor_id,
            "horizon_hours": horizon,
            "baseline": "persistence",
            "unit": unit,
            "n_aligned_rows": int(len(aligned)),
            "n_train": int(split_at),
            "n_test": int(len(holdout)),
            "mae": None,
            "rmse": None,
            "status": "insufficient_data",
        }

        if len(holdout) >= minimum_holdout_rows:
            errors = holdout["actual"] - holdout["prediction"]
            result["mae"] = float(np.mean(np.abs(errors)))
            result["rmse"] = float(np.sqrt(np.mean(np.square(errors))))
            result["status"] = "evaluated"

        results.append(result)

    return results
