SELECT
    EXTRACT(YEAR FROM observed_at) AS year,
    AVG(temperature_c) AS avg_temp
FROM weather_observations
GROUP BY year
ORDER BY avg_temp DESC
LIMIT 10;