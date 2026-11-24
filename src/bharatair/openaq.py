"""Small OpenAQ API v3 client for hourly sensor observations."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

BASE_URL = "https://api.openaq.org/v3"
DEFAULT_TIMEOUT_SECONDS = 30


class OpenAQClient:
    """Fetch paginated hourly observations for a previously selected sensor."""

    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        if not api_key.strip():
            raise ValueError("An OpenAQ API key is required.")
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": api_key})
        self.timeout = timeout

    def fetch_sensor_hours(
        self,
        sensor_id: int,
        datetime_from: str,
        datetime_to: str,
        page_size: int = 100,
    ) -> pd.DataFrame:
        """Fetch hourly averages for one sensor over a bounded ISO-8601 date range.

        The caller is responsible for verifying that the sensor measures PM2.5
        and belongs to the intended monitoring location.
        """
        if sensor_id <= 0:
            raise ValueError("sensor_id must be a positive integer.")
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000.")

        url = f"{BASE_URL}/sensors/{sensor_id}/hours"
        rows: list[dict[str, Any]] = []
        page = 1

        while True:
            params = {
                "datetime_from": datetime_from,
                "datetime_to": datetime_to,
                "limit": page_size,
                "page": page,
            }
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results", [])

            if not results:
                break

            for item in results:
                rows.append(self._flatten_result(sensor_id, item))

            if len(results) < page_size:
                break
            page += 1

        columns = [
            "sensor_id",
            "datetime_from_utc",
            "datetime_from_local",
            "datetime_to_utc",
            "datetime_to_local",
            "value",
            "parameter",
            "unit",
            "latitude",
            "longitude",
            "coverage_percent",
            "has_flags",
        ]
        return pd.DataFrame(rows, columns=columns)

    @staticmethod
    def _flatten_result(sensor_id: int, item: dict[str, Any]) -> dict[str, Any]:
        start = item.get("datetimeFrom") or {}
        end = item.get("datetimeTo") or {}
        parameter = item.get("parameter") or {}
        coordinates = item.get("coordinates") or {}
        coverage = item.get("coverage") or {}

        return {
            "sensor_id": sensor_id,
            "datetime_from_utc": start.get("utc"),
            "datetime_from_local": start.get("local"),
            "datetime_to_utc": end.get("utc"),
            "datetime_to_local": end.get("local"),
            "value": item.get("value"),
            "parameter": parameter.get("name"),
            "unit": parameter.get("units"),
            "latitude": coordinates.get("latitude"),
            "longitude": coordinates.get("longitude"),
            "coverage_percent": coverage.get("percentCoverage"),
            "has_flags": (item.get("flagInfo") or {}).get("hasFlags"),
        }
