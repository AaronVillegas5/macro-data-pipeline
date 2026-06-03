SELECT
    AVG(temperature_c) AS avg_temp
FROM weather_observations
WHERE DATE_TRUNC('year', observed_at) >= '2000-01-01'
ORDER BY observed_at;