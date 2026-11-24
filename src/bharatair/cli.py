"""Command-line entry point for downloading hourly OpenAQ sensor data."""

from __future__ import annotations

import argparse
from pathlib import Path

from bharatair.config import PROJECT_ROOT, get_openaq_api_key
from bharatair.openaq import OpenAQClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download hourly OpenAQ observations for a selected sensor."
    )
    parser.add_argument("--sensor-id", type=int, required=True)
    parser.add_argument("--date-from", required=True, help="ISO-8601 start datetime.")
    parser.add_argument("--date-to", required=True, help="ISO-8601 end datetime.")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional CSV output path. Defaults to data/raw/openaq_sensor_<id>.csv.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    api_key = get_openaq_api_key()
    client = OpenAQClient(api_key)
    frame = client.fetch_sensor_hours(
        sensor_id=args.sensor_id,
        datetime_from=args.date_from,
        datetime_to=args.date_to,
    )

    output = (
        Path(args.output)
        if args.output
        else PROJECT_ROOT / "data" / "raw" / f"openaq_sensor_{args.sensor_id}.csv"
    )
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"Saved {len(frame)} hourly rows to {output}")


if __name__ == "__main__":
    main()
