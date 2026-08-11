SELECT
    location_id,
    DATE(observed_at) AS observed_at_date,
    AVG(temperature_c) AS avg_daily_temp_c,
    SUM(precipitation_mm) AS total_daily_precipitation_mm
FROM {{ ref('stg_weather_observations') }}
GROUP BY 
    location_id,
    observed_at_date
ORDER BY 
    location_id ASC,
    observed_at_date ASC