-- =============================================================================
-- Query: avg_temp_rolling_30_days
-- Cloud Destination: Google BigQuery
-- Description: Computes a 30-day rolling average of temperature for a given location.
-- 
-- Data Validation & Edge Case Handling:
-- - Uses a Common Table Expression (CTE) to pre-aggregate data at the daily level 
--   (`GROUP BY DATE(observed_at)`). This handles intra-day variations or multiple 
--   observations per day by reducing them to a reliable daily baseline.
-- - Null Handling: The `AVG()` aggregation function inherently ignores NULL 
--   temperature values within the window, preventing them from skewing the mean.
-- - Time-Series Gaps: BigQuery's `ROWS BETWEEN 29 PRECEDING AND CURRENT ROW` operates 
--   on physical rows ordered by date. If there are missing days (gaps) in the data, 
--   the rolling window spans the last 30 observed physical records, rather than strictly 30 calendar days.
-- =============================================================================

WITH DailyAverages AS (
    SELECT
        location_id,
        DATE(observed_at) AS observation_date,
        -- Aggregate intra-day readings to establish a consistent daily baseline
        AVG(temperature_c) AS avg_temp
    FROM macro-data-pipeline-498302.weather_data.observations_v2
    WHERE location_id = 1
    GROUP BY location_id, DATE(observed_at)
)
-- Now compute 30-day rolling average over the daily aggregated baseline
SELECT
    location_id,
    observation_date,
    -- Calculate the moving average spanning the current row and the 29 prior rows.
    AVG(avg_temp) OVER (
        ORDER BY observation_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_avg
FROM DailyAverages;
