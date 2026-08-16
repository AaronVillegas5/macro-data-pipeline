SELECT
    observed_at
FROM {{ ref('stg_weather_observations')}}
WHERE 
    -- Open-Meteo gives forcast for up to midnight of today
    observed_at > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)