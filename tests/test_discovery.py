from bharatair.discovery import flatten_pm25_sensors, is_pm25_parameter


def test_pm25_parameter_matching_is_specific() -> None:
    assert is_pm25_parameter("pm25")
    assert is_pm25_parameter("PM2.5")
    assert not is_pm25_parameter("pm10")
    assert not is_pm25_parameter("particulate matter")


def test_flatten_pm25_sensors_keeps_sensor_and_location_metadata() -> None:
    city = {
        "city": "Bhopal",
        "state": "Madhya Pradesh",
        "search_radius_m": 25000,
    }
    locations = [
        {
            "id": 10,
            "name": "Example monitor",
            "timezone": "Asia/Kolkata",
            "isMonitor": True,
            "isMobile": False,
            "coordinates": {"latitude": 23.2, "longitude": 77.4},
            "provider": {"name": "Example provider"},
            "owner": {"name": "Example owner"},
            "datetimeFirst": {"utc": "2024-01-01T00:00:00Z"},
            "datetimeLast": {"utc": "2025-01-01T00:00:00Z"},
            "sensors": [
                {
                    "id": 101,
                    "name": "PM2.5 sensor",
                    "parameter": {"id": 2, "name": "pm25", "units": "µg/m³"},
                },
                {
                    "id": 102,
                    "name": "PM10 sensor",
                    "parameter": {"id": 1, "name": "pm10", "units": "µg/m³"},
                },
            ],
        }
    ]

    rows = flatten_pm25_sensors(city, locations)

    assert len(rows) == 1
    assert rows[0]["sensor_id"] == 101
    assert rows[0]["city"] == "Bhopal"
    assert rows[0]["provider"] == "Example provider"
    assert rows[0]["unit"] == "µg/m³"
    assert rows[0]["location_first_observation_utc"] == "2024-01-01T00:00:00Z"
