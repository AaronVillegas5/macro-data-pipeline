SELECT
    observed_at
FROM {{ ref('stg_weather_observations')}}
WHERE 
    observed_at > CURRENT_TIMESTAMP