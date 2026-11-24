# Initial data dictionary

The exact source schema can vary by API resource and provider. This is the normalized schema emitted by the initial hourly sensor downloader.

| Field | Meaning |
|---|---|
| `sensor_id` | OpenAQ sensor identifier supplied to the downloader |
| `datetime_from_utc` | Start of the hourly observation interval, UTC |
| `datetime_from_local` | Start of the interval in the source location's local time, when supplied |
| `datetime_to_utc` | End of the hourly observation interval, UTC |
| `datetime_to_local` | End of the interval in local time, when supplied |
| `value` | Hourly aggregated observation as returned by OpenAQ |
| `parameter` | Pollutant/measurement parameter name |
| `unit` | Unit reported by the source |
| `latitude`, `longitude` | Coordinates returned with the observation, when present |
| `coverage_percent` | Coverage percentage supplied by the API, when present |
| `has_flags` | Whether OpenAQ reports flags for the observation |

Do not assume all fields will be populated. Preserve source units and metadata. Before modelling, verify that the selected sensor's parameter is PM2.5 and that units are comparable across included observations.
