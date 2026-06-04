WITH YearlyAverages AS(
    SELECT
        location_id,
        EXTRACT(YEAR FROM observed_at) AS year,
        AVG(temperature_c) AS avg_temp
    FROM 
        macro-data-pipeline-498302.weather_data.observations_v2
    WHERE EXTRACT(YEAR FROM observed_at) < EXTRACT(YEAR FROM CURRENT_DATE())

    GROUP BY
        location_id,
        year
), 
YearlyDifferences AS(   
SELECT 
    location_id,
    year,
    avg_temp - LAG(avg_temp, 1) OVER (
        PARTITION BY location_id
        ORDER BY year
        ) AS yearly_difference
FROM 
    YearlyAverages
ORDER BY
    location_id,
    year
)
SELECT
   location_id,
    AVG(yearly_difference) AS avg_yearly_difference
FROM YearlyDifferences
GROUP BY
    location_id