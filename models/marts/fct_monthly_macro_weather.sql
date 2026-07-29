-- models/marts/fct_monthly_macro_weather.sql
-- Joins monthy weather with economic indicators for that month
WITH monthly_weather AS (
    SELECT * FROM {{ ref('int_monthly_weather_aggregates') }}
),
macro_indicators AS (
    SELECT * FROM {{ ref('int_economic_indicators_pivoted') }}
)
SELECT
    w.location_id,
    w.year_month,
    w.avg_monthly_temp,
    w.total_monthly_precipitation,
    w.subzero_days,
    m.cpi,
    m.unemployment_rate,
    m.gdp
FROM monthly_weather w
LEFT JOIN macro_indicators m 
    ON w.year_month = m.year_month