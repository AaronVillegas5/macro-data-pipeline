SELECT
    location_id,
    observed_at,
    observation_date,
    temperature_c,
    precipitation_mm
FROM {{ ref('stg_weather_observations')}}
GROUP BY
    location_id,
    observed_at,
    observation_date,
    temperature_c,
    precipitation_mm
HAVING
    COUNT(*) > 1

