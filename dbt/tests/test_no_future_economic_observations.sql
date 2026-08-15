-- Fails if an observation claims to be from the future
SELECT
    series_id,
    observed_at
FROM {{ ref('stg_economic_observations') }}
WHERE observed_at > CURRENT_TIMESTAMP