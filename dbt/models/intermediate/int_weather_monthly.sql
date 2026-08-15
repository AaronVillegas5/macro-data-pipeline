SELECT
    location_id,
    FORMAT_DATE('%Y-%m', DATE(observed_at)) AS year_month,
    AVG(temperature_c) AS avg_monthly_temp_c,
    SUM(precipitation_mm) AS total_monthly_precipitation_mm
FROM {{ ref('stg_weather_observations') }}
GROUP BY 
    location_id,
    year_month
ORDER BY 
    location_id ASC,
    year_month ASC