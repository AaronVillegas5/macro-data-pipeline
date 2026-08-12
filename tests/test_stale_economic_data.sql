-- Fails if we haven't received new data for an active series in the last 1 year
WITH latest_observations AS (
    SELECT
        series_id,
        MAX(observed_at) AS most_recent_observation
    FROM {{ ref('stg_economic_observations') }}
    GROUP BY series_id
)

SELECT
    series_id,
    most_recent_observation
FROM latest_observations
-- Using standard standard SQL (adjust INTERVAL syntax based on your warehouse: Postgres/Snowflake/DuckDB etc.)
WHERE most_recent_observation < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
