select
    location_id, time, temperature, rain_probability, wind_speed, apparent_temperature, snapshot_time
from {{ source('raw', 'raw_weather_readings') }}