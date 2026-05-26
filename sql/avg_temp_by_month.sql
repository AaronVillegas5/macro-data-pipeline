SELECT
    DATE_TRUNC('month', observed_at) AS month,
    AVG(temperature_c) AS avg_temp
FROM weather_observations
GROUP BY month
ORDER BY month;