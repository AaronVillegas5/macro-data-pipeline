-- models/staging/stg_weather_observations.sql
{{ config(
    materialized='incremental',
    unique_key=['location_id', 'observed_at']
) }}

SELECT
    location_id,
    CAST(observed_at AS TIMESTAMP) AS observed_at,
    DATE(observed_at) AS observation_date,
    temperature_c,
    COALESCE(precipitation, 0.0) AS precipitation_mm
FROM {{ source('raw_weather', 'observations_v2') }}
WHERE 
    -- Filter out any API forecasted data (streaming buffer prevention)
    observed_at <= TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
{% if is_incremental() %}
  -- Only process records newer than the max date already in target table
  AND observed_at > (SELECT MAX(observed_at) FROM {{ this }})
{% endif %}
QUALIFY ROW_NUMBER() OVER (PARTITION BY location_id, observed_at ORDER BY observed_at DESC) = 1
