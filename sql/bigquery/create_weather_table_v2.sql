CREATE TABLE `macro-data-pipeline-498302.weather_data.observations_v2` (
    location_id INT64,
    temperature_c FLOAT64,
    wind_speed FLOAT64,
    observed_at TIMESTAMP,
    pressure FLOAT64,
    humidity FLOAT64,
    created_at TIMESTAMP
)
CLUSTER BY location_id;