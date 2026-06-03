SELECT
    '2000_and_after' AS period,
    AVG(temperature_c) AS avg_temp
FROM weather_observations
WHERE observed_at >= '2000-01-01'

UNION ALL

SELECT
    'before_2000' AS period,
    AVG(temperature_c) AS avg_temp
FROM weather_observations
WHERE observed_at < '2000-01-01';