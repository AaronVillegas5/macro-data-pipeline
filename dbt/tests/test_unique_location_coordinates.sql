-- tests/test_unique_location_coordinates.sql
-- Fails if any latitude/longitude pair appears more than once
SELECT
    latitude,
    longitude,
    COUNT(*) AS duplicate_count
FROM {{ ref('stg_locations') }}
GROUP BY 
    latitude,
    longitude
HAVING COUNT(*) > 1