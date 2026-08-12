-- Want weather my month
WITH weather_data AS (
    SELECT
        location_id,
        -- observed_at,  TIMESTAMP, don't need when aggegrating by month
        observation_date,
        FORMAT_DATE('%Y-%m', DATE(observed_at)) AS year_month,
        temperature_c,
        precipitation_mm
    FROM {{ ref('stg_weather_observations') }}
)
SELECT
    location_id,
    year_month,
    ROUND(AVG(temperature_c), 2) AS avg_monthly_temp_c,
    ROUND(SUM(precipitation_mm), 2) AS total_monthly_precipitation_mm,

    SUM(CASE WHEN temperature_c < 0 THEN 1 ELSE 0 END) AS subzero_days

FROM weather_data
GROUP BY 
    location_id,
    year_month