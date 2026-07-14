import requests
import pandas as pd
import math
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

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
        delta_lon = (distance_km * math.sin(angle)) / (111 * math.cos(math.radians(lat)))

        new_lat = lat + delta_lat
        new_lon = lon + delta_lon
        points.append({
            "location_id": locationId,
            "latitude": new_lat,
            "longitude": new_lon
        })

    return points


def get_hourly_weather(lat, lon, location_id):
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,wind_speed_10m&forecast_hours=6")
    data = response.json()
    hourly = data['hourly']

    readings = []
    for i in range(len(hourly['time'])):
        readings.append({
            "location_id": location_id,
            "time": hourly['time'][i],
            "temperature": hourly['temperature_2m'][i],
            "rain_probability": hourly['precipitation_probability'][i],
            "wind_speed": hourly['wind_speed_10m'][i]
        })

    return readings


load_dotenv()
postcode = os.getenv("POSTCODE")

response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
data = response.json()
longitude = data['result']['longitude']
latitude = data['result']['latitude']
home_location = {
    "location_id": "home",
    "latitude": latitude,
    "longitude": longitude
}



ring_points = generate_ring(latitude, longitude, 30)
ringlocations = [home_location] + ring_points

all_readings = []
for point in ringlocations:
    readings = get_hourly_weather(point["latitude"], point["longitude"], point["location_id"])
    all_readings.extend(readings)

df = pd.DataFrame(all_readings)
print(df)

try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    cursor = conn.cursor()
    print("Connected to Postgres successfully")
except Exception as e:
    print("Failed to connect:", e)

cursor.execute("Truncate table raw_weather_readings")
cursor.execute("Truncate table raw_locations")
for loc in ringlocations:
    cursor.execute(
        "INSERT INTO raw_locations (location_id, latitude, longitude) VALUES (%s, %s, %s) ON CONFLICT (location_id) DO NOTHING",
        (loc["location_id"], loc["latitude"], loc["longitude"])
    )

for reading in all_readings:
    cursor.execute(
        "INSERT INTO raw_weather_readings (location_id, time, temperature, rain_probability, wind_speed) VALUES (%s, %s, %s, %s, %s)",
        (reading["location_id"], reading["time"], reading["temperature"], reading["rain_probability"], reading["wind_speed"])
    )

conn.commit()
cursor.close()
conn.close()