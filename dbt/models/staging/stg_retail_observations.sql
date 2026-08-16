{{ config(
    materialized='incremental',
    unique_key=['naics_code', 'observed_date']
) }}
SELECT
    {{ dbt_utils.generate_surrogate_key(['naics_code', 'observed_at']) }} AS observation_id,
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
