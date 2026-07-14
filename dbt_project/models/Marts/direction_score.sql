with home_temp as (
    select
        time,
        temperature as home_temperature
    from {{ ref('stg_weather_readings') }}
    where location_id = 'home'
),

banded as (
    select
        case
            when r.location_id = 'home' then 'Home'
            when r.location_id = '0' then 'North'
            when r.location_id = '1' then 'North East'
            when r.location_id = '2' then 'East'
            when r.location_id = '3' then 'South East'
            when r.location_id = '4' then 'South'
            when r.location_id = '5' then 'South West'
            when r.location_id = '6' then 'West'
            when r.location_id = '7' then 'North West'
            else r.location_id
        end as location_direction,
        r.time,
        r.temperature,
        r.rain_probability,
        r.wind_speed,
        h.home_temperature,
        case
            when h.home_temperature > 20 then 'hot'
            when h.home_temperature < 15 then 'cold'
            else 'mild'
        end as band
    from {{ ref('stg_weather_readings') }} r
    join home_temp h on r.time = h.time
),

flagged as (
    select
        *,
        case
            when band = 'hot' then true
            when rain_probability > 50 then false
            else true
        end as eligible,
        max(temperature) over (partition by time) as hottest_this_hour,
        min(temperature) over (partition by time) as coolest_this_hour,
        case when temperature = max(temperature) over (partition by time) then true else false end as is_hottest,
        case when temperature = min(temperature) over (partition by time) then true else false end as is_coolest,
        round(temperature) as temp_bucket,
        max(wind_speed) over (partition by time, round(temperature)) as bucket_max_wind,
        min(wind_speed) over (partition by time, round(temperature)) as bucket_min_wind
    from banded
)

select
    *,
    case
        when eligible then rank() over (
            partition by time, eligible
            order by
                case when band = 'hot' then temp_bucket end asc,
                case
                    when band = 'hot' and (bucket_max_wind - bucket_min_wind) >= 5 then -wind_speed
                    when band = 'hot' then temperature
                end asc,
                case when band = 'mild' then wind_speed end asc,
                case when band = 'cold' then temperature end desc
        )
    end as recommendation_rank
from flagged