# Weekend Weather Direction Advisor

A self-hosted dashboard that recommends which direction to travel to walk
the dog based on local weather conditions — comparing home against a ring
of surrounding locations and surfacing whichever feels most comfortable,
hour by hour over the next 6 hours.

## Why this project exists

This is a personal learning project built to gain practical, portfolio-worthy
data engineering skills: **Git, dbt, Python, and Docker** — layered on top of
existing strengths in SQL and DAX. The dashboard itself is a vehicle for
learning; the real goal is hands-on experience with the full pipeline below,
deployed for zero recurring cost.

## Architecture

```
[Postcode config] -> [Geocoding] -> [Weather API]
                                       |
                                       v
                    [Raw tables in Postgres] -> [dbt] -> [Scored tables] -> [Flask + Leaflet UI]
```

- Developed on Windows, to be containerised with Docker later, deployed
  unchanged to a Raspberry Pi on the home network.
- Config-driven: a postcode setting determines the centre point; a ring of
  8 surrounding locations (+ home) is generated from it.

## Tech stack

- **Ingestion**: Python (`requests`, `psycopg2`) — geocoding via postcodes.io, weather via Open-Meteo
- **Storage**: Postgres
- **Transform**: dbt (staging + mart models, tests)
- **Serving**: Flask + Leaflet.js (OpenStreetMap tiles)
- **Packaging**: Docker + docker-compose, multi-arch (Windows dev -> Pi ARM) — not yet started

## Project structure

```
ingestion/              # Python: geocode, generate ring, fetch weather, write raw tables
dbt_project/
  models/staging/       # stg_locations, stg_weather_readings — plain passthroughs + schema.yml tests
  models/marts/          # direction_score — scoring logic + schema.yml tests
flask_app/
  app.py                # Queries direction_score + stg_locations, renders the dashboard
  templates/index.html  # Leaflet map (permanent tooltips per location) + hourly outlook table
```

## How the recommendation works

Each hour, home's **apparent temperature** ("feels like" — combines real
temperature, humidity and wind) decides a band:

- Above 20°C (**hot**) — rank locations by apparent temperature ascending (coolest-feeling wins)
- 15-20°C (**mild**) — same, apparent temperature ascending (favours least muggy)
- Below 15°C (**cold**) — apparent temperature descending (warmest-feeling wins)

Any location with rain probability over 50% is excluded in the mild/cold
bands (rain doesn't matter when it's hot). The dashboard shows each of the
next 6 hours' top pick separately, since "best during a hot hour" and "best
during a cold hour" aren't comparable on one scale.

Coastal/sea detection for ring points (using postcodes.io's nearest-postcode
distance) is planned but not yet built.

## Status

Phase 1 (outdoor-only, PC-based) — Python ingestion, dbt, and the Flask +
Leaflet dashboard are all working end to end. See the project plan and
progress tracker (in the `Claude` folder, outside this repo) for full detail.
Docker/Pi deployment not yet started.

## Setup

1. Create `.env` in the project root with: `DB_HOST`, `DB_PORT`, `DB_NAME`,
   `DB_USER`, `DB_PASSWORD`, `POSTCODE` (not committed — see `.gitignore`).
2. `python -m venv venv` then activate it, then `pip install -r requirements.txt`.
   Note: dbt-core currently requires Python 3.12 or earlier (not 3.13/3.14)
   due to a dependency (`mashumaro`) compatibility gap.
3. Create the `weather_direction` Postgres database and run the `CREATE TABLE`
   statements for `raw_locations` and `raw_weather_readings` (see dbt sources
   in `dbt_project/models/staging/sources.yml` for expected shape).
4. `python ingestion/ingest.py` to populate the raw tables.
5. `cd dbt_project`, `dbt run`, `dbt test`.
6. `cd ../flask_app`, `python app.py`, visit `http://127.0.0.1:5000`.
