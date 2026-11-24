"""Discover candidate PM2.5 sensors near configured Indian city centres."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
import requests

from bharatair.openaq import BASE_URL


def normalize_parameter_name(value: object) -> str:
    """Normalize parameter labels such as 'PM2.5' and 'pm25' for matching."""
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


def is_pm25_parameter(value: object) -> bool:
    """Return True only for common PM2.5 labels, not PM10 or generic particulate matter."""
    return normalize_parameter_name(value) in {"pm25", "particulatematter25"}


def flatten_pm25_sensors(
    city: dict[str, Any], locations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Flatten OpenAQ location responses to one row per PM2.5 sensor."""
    rows: list[dict[str, Any]] = []

    for location in locations:
        coordinates = location.get("coordinates") or {}
        provider = location.get("provider") or {}
        owner = location.get("owner") or {}
        first = location.get("datetimeFirst") or {}
        last = location.get("datetimeLast") or {}
        licenses = location.get("licenses") or []
        license_names = "; ".join(
            str(item.get("name"))
            for item in licenses
            if item.get("name")
        )
        attribution = "; ".join(
            str((item.get("attribution") or {}).get("name"))
            for item in licenses
            if (item.get("attribution") or {}).get("name")
        )

        for sensor in location.get("sensors") or []:
            parameter = sensor.get("parameter") or {}
            parameter_name = parameter.get("name")
            if not is_pm25_parameter(parameter_name):
                continue

            rows.append(
                {
                    "city": city["city"],
                    "state": city.get("state", ""),
                    "search_radius_m": city["search_radius_m"],
                    "location_id": location.get("id"),
                    "location_name": location.get("name"),
                    "locality": location.get("locality"),
                    "timezone": location.get("timezone"),
                    "is_monitor": location.get("isMonitor"),
                    "is_mobile": location.get("isMobile"),
                    "provider": provider.get("name"),
                    "owner": owner.get("name"),
                    "sensor_id": sensor.get("id"),
                    "sensor_name": sensor.get("name"),
                    "parameter": parameter_name,
                    "parameter_id": parameter.get("id"),
                    "unit": parameter.get("units"),
                    "latitude": coordinates.get("latitude"),
                    "longitude": coordinates.get("longitude"),
                    # These are location-level metadata, not sensor-specific guarantees.
                    "location_first_observation_utc": first.get("utc"),
                    "location_last_observation_utc": last.get("utc"),
                    "license_names": license_names,
                    "attribution": attribution,
                }
            )

    return rows


def discover_city_pm25_sensors(
    session: requests.Session,
    api_key: str,
    city: dict[str, Any],
    country_iso: str = "IN",
    page_size: int = 1000,
) -> list[dict[str, Any]]:
    """Search locations within the configured city radius and return PM2.5 sensors."""
    if not 1 <= page_size <= 1000:
        raise ValueError("page_size must be between 1 and 1000.")

    url = f"{BASE_URL}/locations"
    headers = {"X-API-Key": api_key}
    params_base = {
        "coordinates": f"{city['latitude']},{city['longitude']}",
        "radius": city["search_radius_m"],
        "iso": country_iso,
        "limit": page_size,
    }
    rows: list[dict[str, Any]] = []
    page = 1

    while True:
        params = {**params_base, "page": page}
        response = session.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        locations = payload.get("results") or []
        rows.extend(flatten_pm25_sensors(city, locations))

        if len(locations) < page_size:
            break
        page += 1

    return rows


def discover_configured_cities(
    session: requests.Session,
    api_key: str,
    cities_config: dict[str, Any],
) -> pd.DataFrame:
    """Run the PM2.5 sensor discovery for each configured city."""
    rows: list[dict[str, Any]] = []
    radius = int(cities_config.get("search_radius_m", 25000))
    country_iso = str(cities_config.get("country_iso", "IN"))

    for city_config in cities_config.get("cities", []):
        city = {**city_config, "search_radius_m": radius}
        rows.extend(
            discover_city_pm25_sensors(
                session=session,
                api_key=api_key,
                city=city,
                country_iso=country_iso,
            )
        )

    columns = [
        "city",
        "state",
        "search_radius_m",
        "location_id",
        "location_name",
        "locality",
        "timezone",
        "is_monitor",
        "is_mobile",
        "provider",
        "owner",
        "sensor_id",
        "sensor_name",
        "parameter",
        "parameter_id",
        "unit",
        "latitude",
        "longitude",
        "location_first_observation_utc",
        "location_last_observation_utc",
        "license_names",
        "attribution",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    if not frame.empty:
        frame = frame.drop_duplicates(subset=["city", "sensor_id"])
        frame = frame.sort_values(["city", "location_name", "sensor_id"])
    return frame
