CREATE TABLE IF NOT EXISTS public.raw_weather_readings
(
    id SERIAL PRIMARY KEY,
    location_id text NOT NULL,
    "time" timestamp without time zone NOT NULL,
    temperature numeric,
    rain_probability numeric,
    wind_speed numeric,
    apparent_temperature numeric
);

CREATE TABLE IF NOT EXISTS public.raw_locations
(
    location_id text NOT NULL,
    latitude numeric NOT NULL,
    longitude numeric NOT NULL,
    CONSTRAINT raw_locations_pkey PRIMARY KEY (location_id)
);