WITH economic_stg AS(
    SELECT
    series_id,
    value,
    year_month
FROM {{ ref('stg_economic_observations') }}
)
SELECT
    year_month,
    MAX(CASE WHEN series_id = 'CPIAUCSL' THEN value END) AS cpi,
    MAX(CASE WHEN series_id = 'UNRATE' THEN value END) AS unemployment_rate,
    MAX(CASE WHEN series_id = 'GDP' THEN value END) AS gdp
FROM economic_stg
GROUP BY
    year_month