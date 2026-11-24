import pandas as pd

from bharatair.forecast import evaluate_persistence_baselines


def test_persistence_baseline_uses_chronological_holdout() -> None:
    timestamps = pd.date_range("2025-01-01", periods=100, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "datetime_from_utc": timestamps.astype(str),
            "value": range(100),
            "unit": ["µg/m³"] * 100,
        }
    )

    result = evaluate_persistence_baselines(frame, sensor_id=123, horizons_hours=(6,))

    assert len(result) == 1
    assert result[0]["status"] == "evaluated"
    assert result[0]["sensor_id"] == 123
    assert result[0]["horizon_hours"] == 6
    assert result[0]["n_test"] > 0
    assert result[0]["mae"] == 6.0
    assert result[0]["rmse"] == 6.0


def test_persistence_baseline_does_not_fill_missing_hours() -> None:
    timestamps = pd.date_range("2025-01-01", periods=50, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "datetime_from_utc": timestamps.delete([10, 11]).astype(str),
            "value": list(range(48)),
        }
    )

    result = evaluate_persistence_baselines(frame, sensor_id=1, horizons_hours=(1,))

    assert result[0]["n_aligned_rows"] < 48
