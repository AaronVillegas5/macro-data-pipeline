SELECT
    EXTRACT(YEAR FROM observed_at) AS year,
    COALESCE(SUM(precipitation), 0) AS total_rain
FROM weather_observations
GROUP BY year
ORDER BY year;