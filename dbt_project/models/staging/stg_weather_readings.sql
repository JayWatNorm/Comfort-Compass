select
    location_id, time, temperature, rain_probability, wind_speed
from {{ source('raw', 'raw_weather_readings') }}