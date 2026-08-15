SELECT
    location_id,
    observed_at,
    temperature_c,
    precipitation_mm,
    CASE 
        WHEN temperature_c > 90 THEN 'temp_too_high'
        WHEN temperature_c < -100 THEN 'temp_too_low'
        WHEN precipitation_mm > 2000 THEN 'precip_too_high'
        WHEN precipitation_mm < 0 THEN 'precip_negative'
    END AS failure_reason
FROM {{ ref('stg_weather_observations')}}
WHERE 
    temperature_c > 90
    OR temperature_c < -100
    OR precipitation_mm > 2000
    OR precipitation_mm < 0
