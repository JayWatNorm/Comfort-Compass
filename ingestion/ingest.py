import math
import os
from datetime import datetime

import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")


def generate_ring(lat, lon, distance_km):
    bearings = [0, 45, 90, 135, 180, 225, 270, 315]
    points = []

    for locationId, bearing in enumerate(bearings):
        angle = math.radians(bearing)
        delta_lat = (distance_km * math.cos(angle)) / 111
        delta_lon = (distance_km * math.sin(angle)) / (
            111 * math.cos(math.radians(lat))
        )

        new_lat = lat + delta_lat
        new_lon = lon + delta_lon

        checkdistance = requests.get(
            f"https://api.postcodes.io/postcodes?lon={new_lon}&lat={new_lat}&wideSearch=true",
            timeout=10,
        )
        result = checkdistance.json()["result"]

        if not result:
            # Nothing within 20km at all (wideSearch's own cap) - essentially
            # open sea, far from any coastline. No postcode to pull back to,
            # so this ring point is dropped rather than stored with bad data.
            print(
                f"No postcode found near point {locationId} ({new_lat}, {new_lon}) - skipping"
            )
            continue

        nearest = result[0]
        closestpostcodedistance = nearest["distance"]

        if closestpostcodedistance >= 2000:
            # Ring point is at least 2km from the nearest postcode (likely
            # sea) - pull it back to the nearest postcode's own coordinates.
            new_lat = nearest["latitude"]
            new_lon = nearest["longitude"]

        points.append(
            {
                "location_id": locationId,
                "latitude": new_lat,
                "longitude": new_lon,
                "nearest_location_distance": closestpostcodedistance,
            }
        )

    return points


def get_hourly_weather(lat, lon, location_id):
    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,wind_speed_10m,apparent_temperature&forecast_hours=6&timezone=Europe/London",
        timeout=10,
    )
    data = response.json()
    hourly = data["hourly"]

    readings = []
    for i in range(len(hourly["time"])):
        readings.append(
            {
                "location_id": location_id,
                "time": hourly["time"][i],
                "temperature": hourly["temperature_2m"][i],
                "rain_probability": hourly["precipitation_probability"][i],
                "wind_speed": hourly["wind_speed_10m"][i],
                "apparent_temperature": hourly["apparent_temperature"][i],
            }
        )

    return readings


def run_ingestion(postcode):
    response = requests.get(
        f"https://api.postcodes.io/postcodes/{postcode}", timeout=10
    )
    if response.status_code != 200:
        status = f"Error fetching postcode data: {response.status_code}"
        print(status)
        return status
    else:
        data = response.json()
        longitude = data["result"]["longitude"]
        latitude = data["result"]["latitude"]
        # Deliberately naive/local UK time. Open-Meteo is requested with
        # timezone=Europe/London, so its returned `time` values are already
        # UK local; snapshot_time has to match that convention or the mart's
        # join on time would compare a UK-local forecast hour against a UTC
        # stamp and silently mismatch during BST.
        snapshot_time = datetime.now()  # noqa: DTZ005

        home_location = {
            "location_id": "home",
            "latitude": latitude,
            "longitude": longitude,
            "nearest_location_distance": 0,
            "home_postcode": postcode,
            "snapshot_time": snapshot_time,
        }

        ring_points = generate_ring(latitude, longitude, 30)
        for point in ring_points:
            point["home_postcode"] = postcode
            point["snapshot_time"] = snapshot_time

        ringlocations = [home_location] + ring_points

        all_readings = []
        for point in ringlocations:
            readings = get_hourly_weather(
                point["latitude"], point["longitude"], point["location_id"]
            )
            for reading in readings:
                reading["snapshot_time"] = snapshot_time
            all_readings.extend(readings)

        df = pd.DataFrame(all_readings)
        print(df)

        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
        )
        cursor = conn.cursor()

        for loc in ringlocations:
            cursor.execute(
                "INSERT INTO raw_locations (location_id, home_postcode, latitude, longitude, nearest_location_distance, snapshot_time) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    loc["location_id"],
                    loc["home_postcode"],
                    loc["latitude"],
                    loc["longitude"],
                    loc["nearest_location_distance"],
                    loc["snapshot_time"],
                ),
            )

        for reading in all_readings:
            cursor.execute(
                "INSERT INTO raw_weather_readings (location_id, time, temperature, rain_probability, wind_speed, apparent_temperature, snapshot_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    reading["location_id"],
                    reading["time"],
                    reading["temperature"],
                    reading["rain_probability"],
                    reading["wind_speed"],
                    reading["apparent_temperature"],
                    reading["snapshot_time"],
                ),
            )

        conn.commit()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    postcode = os.getenv("POSTCODE")
    run_ingestion(postcode)
