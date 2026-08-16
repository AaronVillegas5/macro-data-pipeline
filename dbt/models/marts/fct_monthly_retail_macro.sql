-- ==============================================================================
-- 📊 Fact Model: Retail, Macroeconomics & Climate
-- ==============================================================================
--
-- BUSINESS REQUIREMENTS:
-- 1. Read from `ref('fct_monthly_macro_weather')` (your existing fact table).
-- 2. Read from `ref('int_retail_pivoted')` (the new retail intermediate table).
-- 3. JOIN them together on `observed_year` and `observed_month`.
-- 4. This is your "Golden Record" table that the AI Agent and Tableau will query!
-- 
-- RESULTING COLUMNS (Target Schema):
-- - All existing columns from `fct_monthly_macro_weather`
--   (e.g., year, month, location, avg_temp, cpi, unemployment_rate)
-- - total_retail_sales_millions
-- - total_retail_sales_yoy_growth_pct
-- - grocery_sales_millions
-- - ecommerce_sales_millions
--
-- WRITE YOUR SQL BELOW:
SELECT
    w.*,
    r.total_retail_sales_millions,
    r.total_retail_sales_yoy_growth_pct,
    r.grocery_sales_millions,
    r.ecommerce_sales_millions,
    r.auto_sales_millions,
    r.clothing_sales_millions
FROM {{ ref('fct_monthly_macro_weather') }} w
LEFT JOIN --keep past weather data pre-1992 intact
    {{ ref('int_retail_pivoted') }} r
ON 
    w.year_month = FORMAT('%d-%02d', r.observed_year, r.observed_month)
