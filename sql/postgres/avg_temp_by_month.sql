SELECT
    w.location_id,
    l.name AS city,
    EXTRACT(YEAR FROM w.observed_at) AS year,
    EXTRACT(MONTH FROM observed_at) AS month,
    AVG(temperature_c) AS avg_temp
FROM weather_observations w
INNER JOIN locations l 
    ON w.location_id = l.id
GROUP BY 
    w.location_id, 
    l.name, 
    year
ORDER BY 
    l.name, 
    year, 
    month;