"""Initial, deliberately transparent checks for hourly air-quality extracts."""

from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_COLUMNS = {"datetime_from_utc", "value"}


def summarize_hourly_data(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarize common quality issues without silently altering observations."""
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(sorted(missing_columns))
        )

    timestamps = pd.to_datetime(frame["datetime_from_utc"], utc=True, errors="coerce")
    values = pd.to_numeric(frame["value"], errors="coerce")

    valid_timestamps = timestamps.notna()
    valid_values = values.notna()
    duplicate_timestamps = int(timestamps[valid_timestamps].duplicated().sum())

    return {
        "row_count": int(len(frame)),
        "missing_or_invalid_timestamps": int((~valid_timestamps).sum()),
        "missing_or_non_numeric_values": int((~valid_values).sum()),
        "negative_values": int((values.dropna() < 0).sum()),
        "duplicate_timestamps": duplicate_timestamps,
        "timestamp_start_utc": (
            timestamps[valid_timestamps].min().isoformat()
            if valid_timestamps.any()
            else None
        ),
        "timestamp_end_utc": (
            timestamps[valid_timestamps].max().isoformat()
            if valid_timestamps.any()
            else None
        ),
    }
