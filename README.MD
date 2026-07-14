# Weekend Weather Direction Advisor

A self-hosted dashboard that recommends which direction to travel at the
weekend based on local weather conditions — e.g. "it's raining south of
us but mild north, so head north."

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

- Developed on Windows, containerised with Docker, deployed unchanged to a
  Raspberry Pi on the home network.
- Config-driven: a postcode setting determines the centre point; a ring of
  surrounding locations is generated from it.

## Tech stack

- **Ingestion**: Python (`requests`) — geocoding via postcodes.io, weather via Open-Meteo
- **Storage**: Postgres
- **Transform**: dbt (staging + mart models, tests)
- **Serving**: Flask + Leaflet.js (OpenStreetMap tiles)
- **Packaging**: Docker + docker-compose, multi-arch (Windows dev -> Pi ARM)

## Project structure

```
ingestion/      # Python scripts: geocode, fetch weather, load raw tables
dbt_project/    # dbt models: staging -> mart (scoring logic)
flask_app/      # Serving layer, reads only from dbt's mart table
```

## Status

Phase 1 (outdoor-only, PC-based) in progress. See project plan for full
build order and Phase 2 (indoor sensor) scope.

## Setup

_To be filled in as ingestion/dbt/Flask pieces come online._
