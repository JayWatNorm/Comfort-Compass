CREATE TABLE IF NOT EXISTS public.raw_weather_readings
(
    id SERIAL PRIMARY KEY,
    location_id text NOT NULL,
    "time" timestamp without time zone NOT NULL,
    temperature numeric,
    rain_probability numeric,
    wind_speed numeric,
    apparent_temperature numeric,
    snapshot_time timestamp without time zone NOT NULL
);

CREATE TABLE IF NOT EXISTS public.raw_locations
(
    id SERIAL PRIMARY KEY,
    location_id text NOT NULL,
    home_postcode text NOT NULL,
    latitude numeric NOT NULL,
    longitude numeric NOT NULL,
    nearest_location_distance int,
    snapshot_time timestamp without time zone NOT NULL
);
