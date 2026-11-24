# Automated workflow setup

The repository automates repeatable data and engineering tasks. It does **not** make research decisions such as declaring a monitor representative of an entire city or selecting the best model without review.

## One-time OpenAQ credential setup

1. Create an API key through the [OpenAQ Explorer](https://explore.openaq.org/register).
2. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
3. Under **Repository secrets**, choose **New repository secret**.
4. Name it exactly `OPENAQ_API_KEY`.
5. Paste the key as its value and save it.

The key is passed to the workflow as a secret. Do not put it in a committed file, issue, notebook, workflow YAML, or chat message. OpenAQ requires the `X-API-Key` request header. See the [official API key instructions](https://docs.openaq.org/using-the-api/api-key).

## What runs automatically

The **OpenAQ Data Refresh** workflow is scheduled weekly and can also be started manually from **Actions**.

Each run:
1. Searches a 25 km radius around the approximate centre points in `config/cities.json` for OpenAQ locations in India.
2. Produces a candidate PM2.5 sensor inventory in `sensor-audit.csv`.
3. Downloads the last configured number of days (default 180) only for sensors explicitly approved in `config/selected_sensors.csv`.
4. Produces per-sensor data-quality summaries.
5. Evaluates persistence baselines at 6-hour and 24-hour horizons using chronological holdout observations.
6. Uploads reports and downloaded extracts as a GitHub Actions artifact (30-day retention).

The workflow does not commit downloaded datasets or create daily artificial commits. Artifacts are available from the workflow run page.

## Review and approve sensors

1. Open the latest **OpenAQ Data Refresh** workflow run.
2. Download the `bharatair-pipeline-output` artifact.
3. Review `sensor-audit.csv` for sensor parameter, units, provider, location metadata, and reported location-level date coverage.
4. Check the original provider/monitor details and license or attribution requirements.
5. Add only reviewed sensors to `config/selected_sensors.csv`, for example:

```csv
city,sensor_id,parameter,unit,approved,notes
Bhopal,12345,pm25,µg/m³,true,Reviewed provider and location metadata
```

The example sensor ID above is a placeholder, not a real or recommended Bhopal sensor. Do not approve it unless it matches a sensor from the audit and you have reviewed its metadata. Keep `approved` as `false` until the review is complete.

A 25 km coordinate search is an initial discovery filter, not an administrative city boundary or proof of city representativeness. The first/last observation dates returned in the location metadata are location-level fields, not a guarantee of coverage for each sensor.

## Run manually

- Go to **Actions → OpenAQ Data Refresh → Run workflow**.
- Choose a history window between 7 and 365 days.
- Confirm the workflow has access to the `OPENAQ_API_KEY` secret.

## Local Windows run

After cloning the project and installing its development dependencies:

```powershell
Copy-Item .env.example .env
# Add OPENAQ_API_KEY=... to .env using a text editor.
python -m bharatair.pipeline --history-days 180
```

Generated files are written to `run-output/`, which is ignored by Git.

## Rate limits and responsible access

The workflow runs weekly rather than polling continuously. OpenAQ's published free tier currently lists 60 requests per minute and 2,000 per hour; the client uses paginated requests and a bounded history window. If the API returns 429, respect the reset period and do not repeatedly rerun the workflow. See [OpenAQ rate limits](https://docs.openaq.org/using-the-api/rate-limits) and [pagination guidance](https://docs.openaq.org/using-the-api/pagination).

## Research review remains necessary

- Inspect coverage and data quality before selecting a sensor.
- Confirm consistent measurement units before combining data.
- Use chronological validation; do not randomly shuffle time-series data.
- Treat persistence metrics as baselines, not proof that a forecasting model is useful.
- Report limitations, sample sizes, and failed experiments honestly.
