-- 2. The Agricultural Freeze Streak (Gaps and Islands)

-- The Concept: A single freezing day damages crops, but a streak of 5+ consecutive freezing days devastates agricultural yields and impacts futures markets.
-- Your Task: Identify the longest consecutive streaks of days where the temperature stayed below 0°C for each city.

WITH DailyTemperatures AS (
    SELECT 
        location_id,
        DATE(observed_at) AS observation_date,
        AVG(temperature_c) AS daily_temp
    FROM
        `macro-data-pipeline-498302.weather_data.observations_v2`
    GROUP BY
        location_id,
        DATE(observed_at)
    HAVING AVG(temperature_c) < 0
),
SubzeroDays AS (
    SELECT
        location_id,
        observation_date,
        daily_temp,
        DATE_SUB(observation_date, INTERVAL row_num DAY) AS grp
    FROM
    --Subquery to add row numbers to DailyTemperatures CTE
        (SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY location_id ORDER BY observation_date) AS row_num
         FROM 
            DailyTemperatures
        )
)
SELECT
    l.name,
    COALESCE(MAX(streak_length),0) AS longest_streak
FROM (SELECT
        location_id,
        grp,
        COUNT(*) AS streak_length
    FROM
        SubzeroDays
    GROUP BY
        location_id,
        grp
    ) s
RIGHT JOIN `macro-data-pipeline-498302.weather_data.locations` l
    ON l.id = s.location_id
GROUP BY
    l.id,
    l.name
ORDER BY 
    l.id ASC;