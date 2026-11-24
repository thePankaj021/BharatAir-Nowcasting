"""Run the repeatable weekly OpenAQ audit and approved-sensor refresh."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from bharatair.config import PROJECT_ROOT, get_openaq_api_key
from bharatair.data_quality import summarize_hourly_data
from bharatair.discovery import discover_configured_cities, is_pm25_parameter
from bharatair.forecast import evaluate_persistence_baselines
from bharatair.openaq import OpenAQClient


def _approved_sensor_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    registry = pd.read_csv(path, dtype=str).fillna("")
    required = {"city", "sensor_id", "parameter", "approved"}
    missing = required.difference(registry.columns)
    if missing:
        raise ValueError(
            "Sensor registry is missing columns: " + ", ".join(sorted(missing))
        )

    approved: list[dict[str, str]] = []
    for row in registry.to_dict(orient="records"):
        is_approved = row["approved"].strip().casefold() in {"true", "yes", "1"}
        if not is_approved:
            continue
        if not is_pm25_parameter(row["parameter"]):
            raise ValueError(
                f"Approved sensor {row['sensor_id']} is not labelled as PM2.5. "
                "Check the audit and registry before downloading."
            )
        if not row["sensor_id"].isdigit():
            raise ValueError(f"Invalid sensor ID in registry: {row['sensor_id']!r}")
        approved.append(row)
    return approved


def run_pipeline(
    api_key: str,
    cities_path: Path,
    sensors_path: Path,
    output_dir: Path,
    history_days: int = 180,
) -> dict[str, Any]:
    if history_days < 7 or history_days > 365:
        raise ValueError("history_days must be between 7 and 365.")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    with cities_path.open(encoding="utf-8") as handle:
        cities_config = json.load(handle)

    session = requests.Session()
    audit = discover_configured_cities(session, api_key, cities_config)
    audit_path = output_dir / "sensor-audit.csv"
    audit.to_csv(audit_path, index=False)

    selected = _approved_sensor_rows(sensors_path)
    client = OpenAQClient(api_key)
    now = datetime.now(UTC).replace(microsecond=0)
    date_to = now.isoformat().replace("+00:00", "Z")
    date_from = (now - timedelta(days=history_days)).isoformat().replace("+00:00", "Z")

    quality_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    for sensor in selected:
        sensor_id = int(sensor["sensor_id"])
        try:
            observations = client.fetch_sensor_hours(
                sensor_id=sensor_id,
                datetime_from=date_from,
                datetime_to=date_to,
                page_size=1000,
            )
            observations.insert(0, "city", sensor["city"])
            raw_path = raw_dir / f"sensor_{sensor_id}.csv"
            observations.to_csv(raw_path, index=False)

            quality = summarize_hourly_data(observations)
            quality.update(
                {
                    "city": sensor["city"],
                    "sensor_id": sensor_id,
                    "registry_unit": sensor.get("unit", ""),
                    "download_file": str(raw_path.relative_to(output_dir)),
                }
            )
            quality_rows.append(quality)
            metric_rows.extend(
                evaluate_persistence_baselines(observations, sensor_id=sensor_id)
            )
        except (requests.RequestException, ValueError) as error:
            error_rows.append(
                {
                    "city": sensor["city"],
                    "sensor_id": sensor_id,
                    "error_type": type(error).__name__,
                    "message": str(error)[:500],
                }
            )

    pd.DataFrame(quality_rows).to_csv(output_dir / "quality-report.csv", index=False)
    pd.DataFrame(
        metric_rows,
        columns=[
            "sensor_id",
            "horizon_hours",
            "baseline",
            "unit",
            "n_aligned_rows",
            "n_train",
            "n_test",
            "mae",
            "rmse",
            "status",
        ],
    ).to_csv(output_dir / "baseline-metrics.csv", index=False)
    pd.DataFrame(
        error_rows, columns=["city", "sensor_id", "error_type", "message"]
    ).to_csv(output_dir / "sensor-errors.csv", index=False)

    summary = {
        "generated_at_utc": now.isoformat(),
        "candidate_pm25_sensors": int(len(audit)),
        "approved_sensors": len(selected),
        "sensors_downloaded": len(quality_rows),
        "sensor_errors": len(error_rows),
        "history_days": history_days,
        "output_directory": str(output_dir),
        "note": (
            "The sensor audit is a candidate inventory, not an automatic city "
            "representativeness decision. Baseline metrics are descriptive and "
            "must be inspected before making model claims."
        ),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    summary_markdown = [
        "# BharatAir automated data pipeline",
        "",
        f"- Generated (UTC): {summary['generated_at_utc']}",
        f"- Candidate PM2.5 sensors found: {summary['candidate_pm25_sensors']}",
        f"- Approved sensors in registry: {summary['approved_sensors']}",
        f"- Sensors downloaded: {summary['sensors_downloaded']}",
        f"- Sensor download errors: {summary['sensor_errors']}",
        f"- History window: {history_days} days",
        "",
        summary["note"],
    ]
    summary_text = "\n".join(summary_markdown) + "\n"
    (output_dir / "SUMMARY.md").write_text(summary_text, encoding="utf-8")
    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        with Path(github_summary).open("a", encoding="utf-8") as handle:
            handle.write(summary_text)

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit OpenAQ PM2.5 sensor availability and refresh approved sensors."
    )
    parser.add_argument(
        "--cities",
        type=Path,
        default=PROJECT_ROOT / "config" / "cities.json",
    )
    parser.add_argument(
        "--sensors",
        type=Path,
        default=PROJECT_ROOT / "config" / "selected_sensors.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "run-output",
    )
    parser.add_argument("--history-days", type=int, default=180)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    api_key = get_openaq_api_key()
    summary = run_pipeline(
        api_key=api_key,
        cities_path=args.cities,
        sensors_path=args.sensors,
        output_dir=args.output,
        history_days=args.history_days,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
