-- ==============================================================================
-- 🛒 Staging Model: U.S. Census Retail Sales (MARTS)
-- ==============================================================================
--
-- BUSINESS REQUIREMENTS:
-- 1. Read from the raw BigQuery table `retail_data.observations`
--    - The raw table has columns: naics_code, category_name, value, observed_at
-- 2. Clean the data:
--    - Ensure `observed_at` is safely cast to a DATE or TIMESTAMP.
--    - Extract the year and month into separate columns for easy joining downstream.
--    - Ensure `value` (which represents Millions of Dollars) is correctly cast to NUMERIC or FLOAT64.
-- 3. Handle anomalies:
--    - Drop or filter out any rows where `value` is null or 0 (if applicable).
-- 
-- RESULTING COLUMNS (Target Schema):
-- - observation_id (surrogate key if you want, e.g. using dbt_utils.generate_surrogate_key)
-- - naics_code (STRING)
-- - category_name (STRING)
-- - sales_millions (NUMERIC/FLOAT64)
-- - observed_date (DATE)
-- - observed_year (INT64)
-- - observed_month (INT64)
--
-- WRITE YOUR SQL BELOW:
{{ config(
    materialized='incremental',
    unique_key=['naics_code', 'observed_date']
) }}
SELECT
    TO_HEX(MD5(CONCAT(naics_code, CAST(observed_at AS STRING)))) AS observation_id,
    naics_code,
    category_name,
    CAST(value AS FLOAT64) AS sales_millions,
    CAST(observed_at AS DATE) as observed_date,
    EXTRACT(YEAR FROM observed_at) AS observed_year,
    EXTRACT(MONTH FROM observed_at) AS observed_month
FROM
    {{ source('retail_data','observations') }}
{% if is_incremental() %}
WHERE observed_at > (SELECT MAX(observed_at) FROM {{ this }})

{% endif %}
-- Keep the most recent record, and deduplicate the rest
QUALIFY ROW_NUMBER() OVER (PARTITION BY naics_code, observed_at ORDER BY observed_at DESC) = 1
