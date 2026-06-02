SELECT
    EXTRACT(YEAR FROM observed_at) AS year,
    SUM(precipitation) AS total_precip
FROM weather_observations
GROUP BY year
ORDER BY total_precip DESC
LIMIT 10;