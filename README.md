# BharatAir-Nowcasting

**Data-quality-aware PM2.5 forecasting for Indian cities using open air-quality observations, reproducible time-series evaluation, and an interactive dashboard.**

[![CI](https://github.com/thePankaj021/BharatAir-Nowcasting/actions/workflows/ci.yml/badge.svg)](https://github.com/thePankaj021/BharatAir-Nowcasting/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

> **Project status: Early development.** The repository currently contains the project specification, an initial OpenAQ hourly-data client, data-quality utilities, and automated tests. City coverage, forecast models, forecast metrics, and the dashboard are not yet established. Results will be reported only after the corresponding experiments have been run.

## Overview

BharatAir-Nowcasting is an applied data science project to investigate short-horizon PM2.5 forecasting for selected Indian cities. The project will start by auditing the availability, completeness, measurement frequency, and provenance of suitable monitoring sensors. It will then build a reproducible pipeline for collecting and validating hourly observations before developing and evaluating forecasting baselines and machine-learning models.

The project is deliberately **data-quality-aware**: a forecast should be accompanied by information about the amount and quality of the observations behind it. Missing measurements, irregular reporting, duplicate timestamps, and sensor coverage will be measured and documented rather than silently hidden.

## Problem statement

Air-quality measurements are collected from monitoring locations with differing coverage and reporting behaviour. A model trained without checking these characteristics can produce misleading forecasts or optimistic evaluation results. This project aims to build a transparent workflow that:

1. identifies suitable PM2.5 sensors and records their metadata;
2. collects hourly observations through a documented public API;
3. checks timestamp consistency, missingness, duplicates, invalid values, and available coverage metadata;
4. establishes simple forecasting baselines before more complex models;
5. evaluates predictions with time-ordered validation and clearly reported metrics; and
6. presents observations, data-quality information, and model forecasts in an accessible dashboard.

## Objectives

- Audit OpenAQ station and sensor availability for candidate Indian cities.
- Build a repeatable data-ingestion process with explicit API authentication and date ranges.
- Preserve raw source responses or raw extracts separately from processed data.
- Produce data-quality summaries before modelling.
- Compare persistence and seasonal-naive baselines with suitable machine-learning models.
- Avoid random train/test splits for time-series evaluation.
- Report errors by city, sensor, forecast horizon, and data-availability conditions where sample sizes permit.
- Explore uncertainty estimates and model/data drift only after a reliable baseline has been established.
- Build a dashboard that communicates limitations as well as forecasts.

## Scope and non-goals

**Initial scope**
- Target pollutant: PM2.5.
- Primary observation frequency: hourly.
- Geography: selected Indian cities, chosen after a sensor-coverage audit.
- Initial data provider: OpenAQ API v3.
- Forecast horizons: candidate horizons of 6 and 24 hours; these will be retained only if the available history supports meaningful evaluation.

**Not claimed at this stage**
- No production-ready forecasting model is available yet.
- No accuracy, RMSE, MAE, or city-level performance result is claimed.
- The project is not an official air-quality alert service and must not be used as the sole basis for health or emergency decisions.
- OpenAQ coverage is not a complete inventory of all monitoring data in India.

## Data source

### OpenAQ API v3

The initial data source is the [OpenAQ API v3](https://docs.openaq.org/). OpenAQ aggregates publicly available air-quality observations from contributing providers. Availability varies by location, provider, pollutant, and time period.

- API overview: https://docs.openaq.org/api
- API key instructions: https://docs.openaq.org/using-the-api/api-key
- Hourly sensor measurements: https://docs.openaq.org/resources/measurements
- API reference: https://api.openaq.org/docs

OpenAQ API v3 requires an API key sent in the `X-API-Key` request header. Create a key through the OpenAQ Explorer and store it locally as `OPENAQ_API_KEY`. Never commit a real key to Git.

The initial downloader accepts a **sensor ID** and a date range. Sensor IDs should be selected only after checking that the sensor measures PM2.5, belongs to the intended location, and has adequate historical coverage. A sensor ID alone is not proof of representativeness for an entire city.

### Data provenance and responsible use

For each selected sensor, record the sensor ID, location ID, provider, parameter, unit, coordinates when supplied, license/attribution information, extraction date, and requested date range. Follow the data provider's terms and attribution requirements. Keep source units intact during ingestion; do not combine values with incompatible units.

## Proposed methodology

### 1. Station and data audit
- Identify candidate locations and PM2.5 sensors.
- Inspect historical depth, temporal resolution, gaps, coverage metadata, and source/provider details.
- Define explicit inclusion and exclusion criteria before choosing cities or sensors.

### 2. Data ingestion
- Retrieve hourly sensor observations with bounded date ranges and pagination.
- Save raw extracts under `data/raw/` and keep processed files separate.
- Record retrieval metadata so an extract can be reproduced.

### 3. Data-quality assessment
- Parse timestamps consistently and retain UTC as the canonical timestamp.
- Identify missing timestamps, duplicate periods, null readings, non-numeric values, and physically implausible values for review.
- Use API coverage metadata where available and make any completeness threshold explicit.
- Do not silently interpolate or remove flagged observations.

### 4. Feature engineering
Candidate features, subject to availability and leakage checks:
- lagged PM2.5 observations;
- rolling means and variability over past windows;
- hour-of-day and day-of-week encodings;
- seasonal/calendar features;
- meteorological variables only if a suitable, documented source is integrated.

All features must be computed using information available at the forecast issue time.

### 5. Forecasting and evaluation
Start with persistence and seasonal-naive baselines. Then evaluate suitable models such as regularized regression, Random Forest, and gradient-boosted trees. A more complex model will be retained only if it improves on appropriate baselines under a defensible time-based evaluation.

Use chronological train/validation/test periods or rolling-origin evaluation. Do not randomly shuffle time-series observations across splits. Candidate metrics include MAE and RMSE, reported in the original measurement unit (typically µg/m³ when supplied by the source). Report sample counts and baseline comparisons alongside metrics.

### 6. Communication
A later dashboard is intended to show historical observations, data-quality indicators, forecast values, and evaluation context. It should clearly distinguish measured values from model estimates and indicate when data are stale or insufficient.

## Repository structure

```text
BharatAir-Nowcasting/
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/
│   ├── raw/              # Local source extracts; not committed
│   └── processed/        # Local processed data; not committed
├── docs/
│   └── DATA_DICTIONARY.md
├── notebooks/            # Exploratory analysis and experiments
├── reports/              # Locally generated reports; not committed
├── scripts/
│   └── download_sensor_data.py
├── src/
│   └── bharatair/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── data_quality.py
│       └── openaq.py
├── tests/
│   └── test_data_quality.py
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## Getting started

### 1. Requirements

- Python 3.10 or later
- Git
- An OpenAQ API key for API downloads

### 2. Clone and create a virtual environment

```bash
git clone https://github.com/thePankaj021/BharatAir-Nowcasting.git
cd BharatAir-Nowcasting

python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 4. Configure the API key

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your OpenAQ API key:

```dotenv
OPENAQ_API_KEY=your_openaq_api_key_here
```

The `.env` file is ignored by Git. Do not paste API keys into source code, notebooks, issues, or commits.

### 5. Download hourly observations for a selected sensor

First identify and verify a PM2.5 sensor using the OpenAQ Explorer and its metadata. Then run:

```bash
python -m bharatair.cli --sensor-id YOUR_SENSOR_ID --date-from 2025-01-01T00:00:00Z --date-to 2025-02-01T00:00:00Z
```

The command writes a CSV beneath `data/raw/`. The date range is illustrative; choose a range supported by the selected sensor. The downloader does not automatically decide which sensors represent a city.

### 6. Run the tests

```bash
python -m pytest
```

## Configuration

| Environment variable | Purpose |
|---|---|
| `OPENAQ_API_KEY` | API key required by OpenAQ API v3 |

See [`.env.example`](.env.example) for the local template. Do not commit credentials.

## Automated data workflow

A weekly GitHub Actions workflow, **OpenAQ Data Refresh**, audits candidate PM2.5 sensors near Bhopal, Indore, and Delhi. It can also refresh hourly observations for sensors that have been explicitly reviewed and approved in `config/selected_sensors.csv`. Each run produces a sensor inventory, data-quality summaries, persistence-baseline metrics, and downloadable data artifacts.

Before the first run, add the repository secret `OPENAQ_API_KEY` under **Settings → Secrets and variables → Actions**. The workflow never stores the key in repository files. See [docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md) for the complete setup and sensor-review process.

The weekly workflow does not invent daily commits or automatically approve sensors. It creates a repeatable audit and evaluation package; sensor selection and research interpretation remain reviewable decisions.

## Development roadmap

- [x] Create repository, project specification, and initial package structure.
- [x] Add an OpenAQ v3 hourly-sensor data client.
- [x] Add initial data-quality checks and unit tests.
- [x] Add city-radius PM2.5 sensor discovery for Bhopal, Indore, and Delhi.
- [x] Add weekly/manual OpenAQ refresh workflow for reviewed sensors.
- [x] Add quality summaries and chronological persistence-baseline evaluation.
- [ ] Audit candidate Indian cities and PM2.5 sensor coverage.
- [ ] Document sensor-selection criteria and chosen sensors.
- [ ] Add ingestion metadata and reproducible extraction manifests.
- [ ] Build exploratory analysis and a data-quality report.
- [ ] Implement persistence and seasonal-naive forecasting baselines.
- [ ] Implement time-based validation and baseline comparisons.
- [ ] Evaluate candidate machine-learning models.
- [ ] Add uncertainty analysis and monitoring where justified.
- [ ] Build and document the dashboard.
- [ ] Package and deploy a reproducible application.

Roadmap checkboxes will be updated as work is completed; they are not claims that the future stages already exist.

## Reproducibility principles

- Keep raw source extracts immutable where practical.
- Record data source, sensor ID, retrieval time, date range, timezone, and units.
- Separate exploratory notebooks from reusable source code.
- Set random seeds for stochastic experiments and record model parameters.
- Use chronological evaluation and avoid target leakage.
- Report failed experiments and limitations, not only the best result.
- Do not commit API keys, private data, or large raw datasets.

## Contributing

This is an individual learning and portfolio project under active development. Suggestions and bug reports are welcome through GitHub Issues. Please include a clear description, steps to reproduce, and relevant environment details. Do not include API keys or personal data in issues.

## License

This project is released under the [MIT License](LICENSE). Data obtained from OpenAQ or its contributing providers may have separate terms and attribution requirements; the repository's software license does not override those terms.

## Acknowledgements

- [OpenAQ](https://openaq.org/) for providing an API to access publicly available air-quality observations.
- The contributing data providers and monitoring organizations whose observations are made available through OpenAQ.

---

**Maintainer:** [@thePankaj021](https://github.com/thePankaj021)
