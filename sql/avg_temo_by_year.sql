SELECT
    DATE_TRUNC('year', observed_at) AS year,
    AVG(temperature_c) AS avg_temp
FROM weather_observations
GROUP BY year
ORDER BY year;