-- models/staging/stg_economic_observations.sql
{{ config(
    materialized='incremental',
    unique_key=['series_id', 'observed_at']
) }}

SELECT
    series_id,
    series_name,
    value,
    CAST(observed_at AS TIMESTAMP) AS observed_at,
    DATE(observed_at) AS observation_date,
    FORMAT_DATE('%Y-%m', DATE(observed_at)) AS year_month
FROM {{ source('raw_economic', 'observations_v2') }}

{% if is_incremental() %}
  -- Only process records newer than the max date already in target table
  WHERE observed_at > (SELECT MAX(observed_at) FROM {{ this }})
{% endif %}