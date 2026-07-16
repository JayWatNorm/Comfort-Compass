select
    location_id, home_postcode, latitude, longitude, nearest_location_distance, snapshot_time
from {{ source('raw', 'raw_locations') }}