WITH YearlyAverages AS(
    SELECT
        location_id,
        EXTRACT(YEAR FROM observed_at) AS year,
        AVG(temperature_c) AS avg_temp
    FROM 
        macro-data-pipeline-498302.weather_data.observations_v2
    GROUP BY
        location_id,
        year
)   
SELECT 
    location_id,
    year,
    avg_temp - LAG(avg_temp, 1) OVER (
        ORDER BY year
        PARTITION BY location_id)
FROM 
    YearlyAverages
ORDER BY
    location_id,
    year

