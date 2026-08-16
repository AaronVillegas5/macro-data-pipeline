-- ==============================================================================
-- ☁️ BigQuery DDL: Create Retail Observations Table
-- ==============================================================================
--
-- BUSINESS REQUIREMENTS:
-- 1. Create the `retail_data` schema/dataset if it doesn't exist.
-- 2. Create the `observations` table inside `retail_data`.
-- 3. The table needs the following columns:
--    - naics_code (STRING, cannot be null)
--    - category_name (STRING)
--    - value (FLOAT64, cannot be null)
--    - observed_at (TIMESTAMP, cannot be null)
-- 4. Optimization:
--    - Partition the table by the DATE of the `observed_at` column.
--    - Cluster the table by `naics_code` for fast filtering.
--
-- WRITE YOUR SQL BELOW:
CREATE SCHEMA IF NOT EXISTS `retail_data`;

CREATE TABLE IF NOT EXISTS `retail_data.observations` (
    naics_code STRING NOT NULL,
    category_name STRING,
    value FLOAT64 NOT NULL,
    observed_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(observed_at)
CLUSTER BY naics_code;
