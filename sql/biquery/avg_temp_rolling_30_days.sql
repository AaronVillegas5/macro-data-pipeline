WITH DailyAverages AS (
  SELECT
      location_id,
      DATE(observed_at) AS observation_date,
      AVG(temperature_c) AS avg_temp
  FROM
      macro-data-pipeline-498302.weather_data.observations_v2
  WHERE 
      location_id = 1
  GROUP BY 
      location_id, DATE(observed_at)
)
-- Now compute 30-day rolling average
SELECT 
    location_id,
    observation_date,
    AVG(avg_temp) OVER (
        ORDER BY observation_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW 
    ) as rolling_avg
FROM DailyAverages