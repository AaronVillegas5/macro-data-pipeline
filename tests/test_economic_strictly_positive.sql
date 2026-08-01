-- Fails if any series that MUST be positive has a negative value
SELECT
    series_id,
    observed_at,
    value
FROM {{ ref('stg_economic_observations') }}
WHERE series_id IN (
    'GDP',           -- Gross Domestic Product
    'CPIAUCSL',      -- Consumer Price Index
    'POP',           -- Population
    'PAYEMS'         -- Total Nonfarm Payrolls
)
AND value < 0
