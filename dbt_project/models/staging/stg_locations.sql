select
    location_id, latitude, longitude
from {{ source('raw', 'raw_locations') }}