import pandas as pd
import pytest

from bharatair.data_quality import summarize_hourly_data


def test_summarize_hourly_data_counts_basic_quality_issues() -> None:
    frame = pd.DataFrame(
        {
            "datetime_from_utc": [
                "2025-01-01T00:00:00Z",
                "2025-01-01T00:00:00Z",
                "not-a-date",
                "2025-01-01T03:00:00Z",
            ],
            "value": [12.5, -1.0, 8.0, None],
        }
    )

    summary = summarize_hourly_data(frame)

    assert summary["row_count"] == 4
    assert summary["missing_or_invalid_timestamps"] == 1
    assert summary["missing_or_non_numeric_values"] == 1
    assert summary["negative_values"] == 1
    assert summary["duplicate_timestamps"] == 1


def test_summarize_hourly_data_requires_expected_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        summarize_hourly_data(pd.DataFrame({"value": [1.0]}))
