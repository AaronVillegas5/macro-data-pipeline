SELECT
    w.location_id,
    l.name AS city,
    EXTRACT(YEAR FROM w.observed_at) AS year,
    COALESCE(SUM(precipitation), 0) AS total_rain
FROM weather_observations w
INNER JOIN locations l 
    ON w.location_id = l.id
GROUP BY w.location_id, l.name, year
ORDER BY l.name, year;