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



{% if is_incremental() %}
  -- Only process records newer than the max date already in target table
  WHERE observed_at > (SELECT MAX(observed_at) FROM {{ this }})
{% endif %}