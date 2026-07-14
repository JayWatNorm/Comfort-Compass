with home_temp as (
    select
        time,
        apparent_temperature as home_apparent_temperature
    from {{ ref('stg_weather_readings') }}
    where location_id = 'home'
),

banded as (
    select
        r.location_id,
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
        r.apparent_temperature,
        r.rain_probability,
        r.wind_speed,
        h.home_apparent_temperature,
        case
            when h.home_apparent_temperature > 20 then 'hot'
            when h.home_apparent_temperature < 15 then 'cold'
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
        max(apparent_temperature) over (partition by time) as hottest_feel_this_hour,
        min(apparent_temperature) over (partition by time) as coolest_feel_this_hour,
        case when apparent_temperature = max(apparent_temperature) over (partition by time) then true else false end as is_hottest,
        case when apparent_temperature = min(apparent_temperature) over (partition by time) then true else false end as is_coolest
    from banded
)

select
    *,
    case
        when eligible then rank() over (
            partition by time, eligible
            order by
                case when band = 'hot' then apparent_temperature end asc,
                case when band = 'mild' then apparent_temperature end asc,
                case when band = 'cold' then apparent_temperature end desc
        )
    end as recommendation_rank,
    case
        when band = 'hot' then 'Feels cooler than nearby areas'
        when band = 'mild' then 'Feels less muggy and more comfortable than nearby areas'
        when band = 'cold' then 'Feels warmer than nearby areas'
    end as reason
from flagged