-- Yearly climate summary per city
WITH streaks AS(
    SELECT *
    FROM {{ ref('int_weather_streaks') }}
),
all_time_weather AS (
    SELECT 
        location_id,
        ROUND(AVG(avg_monthly_temp_c), 2) AS avg_temp_c,
        ROUND(SUM(total_monthly_precipitation_mm)) AS total_precipitation_mm
    FROM {{ ref('int_monthly_weather_aggregates') }}
    GROUP BY
        location_id
)
SELECT
    l.id,
    l.name,
    l.country,
    l.region,
    w.avg_temp_c,
    w.total_precipitation_mm,
    COALESCE(s.longest_subzero_streak, 0) AS longest_subzero_streak
FROM {{ ref('stg_locations') }} l
LEFT JOIN streaks s
    ON l.id = s.location_id
LEFT JOIN all_time_weather w
    ON l.id = w.location_id
ORDER BY
    l.id ASC