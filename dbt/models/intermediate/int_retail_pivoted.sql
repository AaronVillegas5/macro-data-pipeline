-- ==============================================================================
-- 🛒 Intermediate Model: Pivoted Retail Sales
-- ==============================================================================
--
-- BUSINESS REQUIREMENTS:
-- 1. Read from `ref('stg_retail_observations')`
-- 2. The staging model has data in a "long" format (one row per NAICS code per month).
--    We need to PIVOT this into a "wide" format so there is exactly ONE row per month.
-- 3. Calculate Year-over-Year (YoY) Growth for Total Retail Sales.
--    - Hint: Use the `LAG()` window function partitioned by the month and ordered by year, 
--      or simply `LAG(sales, 12) OVER (ORDER BY observed_date)`.
--
-- RESULTING COLUMNS (Target Schema):
-- - observed_year (INT64)
-- - observed_month (INT64)
-- - total_retail_sales_millions (NUMERIC/FLOAT64)
-- - total_retail_sales_yoy_growth_pct (NUMERIC/FLOAT64)  <-- The YoY variance!
-- - grocery_sales_millions (NUMERIC/FLOAT64)
-- - ecommerce_sales_millions (NUMERIC/FLOAT64)
-- - auto_sales_millions (NUMERIC/FLOAT64)
-- - clothing_sales_millions (NUMERIC/FLOAT64)
--
-- WRITE YOUR SQL BELOW:
WITH pivoted_sales AS (
    SELECT
        observed_year,
        observed_month,
        SUM(CASE WHEN naics_code = '44W72' THEN sales_millions ELSE 0 END) AS total_retail_sales_millions,
        SUM(CASE WHEN naics_code = '445' THEN sales_millions ELSE 0 END) AS grocery_sales_millions,
        SUM(CASE WHEN naics_code = '454' THEN sales_millions ELSE 0 END) AS ecommerce_sales_millions,
        SUM(CASE WHEN naics_code = '441' THEN sales_millions ELSE 0 END) AS auto_sales_millions,
        SUM(CASE WHEN naics_code = '448' THEN sales_millions ELSE 0 END) AS clothing_sales_millions
    FROM {{ ref('stg_retail_observations') }}
    GROUP BY 
        observed_year,
        observed_month
)
SELECT
    *,
    -- (current - prev) /prev = change in %
   SAFE_DIVIDE(
    total_retail_sales_millions - LAG(total_retail_sales_millions,12) OVER (ORDER BY observed_year, observed_month),
    LAG(total_retail_sales_millions,12) OVER (ORDER BY observed_year, observed_month)) * 100  AS total_retail_sales_yoy_growth_pct
FROM pivoted_sales
ORDER BY
    observed_year DESC,
    observed_month DESC
