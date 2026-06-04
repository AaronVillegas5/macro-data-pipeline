CREATE OR REPLACE TABLE `macro-data-pipeline-498302.weather_data.observations_v2` 
CLUSTER BY location_id
AS
SELECT * FROM `macro-data-pipeline-498302.weather_data.observations_v2`
QUALIFY ROW_NUMBER() OVER(
    PARTITION BY location_id, observed_at 
    ORDER BY created_at DESC
) = 1;