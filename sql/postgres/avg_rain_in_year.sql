SELECT
    w.location_id,
    l.name AS city,
    AVG(COALESCE(w.precipitation, 0)) * 24 * 365 AS avg_rain
FROM weather_observations w
INNER JOIN locations l ON w.location_id = l.id
GROUP BY w.location_id, l.name
ORDER BY l.name;