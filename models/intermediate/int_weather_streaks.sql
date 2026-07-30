WITH subzero_days AS (
    SELECT
        location_id,
        observation_date,
        AVG(temperature_c) AS temperature_c
    FROM {{ ref('stg_weather_observations') }}
    GROUP BY
        location_id,
        observation_date
    HAVING temperature_c < 0
),
row_nums AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY location_id ORDER BY observation_date) AS row_num
    FROM subzero_days
),
streak_group AS (
    SELECT  

        *,
        DATE_SUB(observation_date, INTERVAL row_num DAY) AS grp
    FROM row_nums
),
streak_count AS (
    SELECT 
        location_id,
        grp,
        COUNT(*) AS streak_length
    FROM streak_group
    GROUP BY
        location_id,
        grp
)
SELECT
    s.location_id,
    l.name,
    COALESCE(MAX(streak_length),0) AS longest_subzero_streak
FROM streak_count s
LEFT JOIN {{ ref('stg_locations')}} l
    ON l.id = s.location_id
GROUP BY 
    s.location_id,
    l.name
ORDER BY 
    s.location_id