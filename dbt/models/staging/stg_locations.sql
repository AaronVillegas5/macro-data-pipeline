SELECT
    id,
    name,
    country,
    region,
    latitude,
    longitude
FROM {{ source('raw_weather','locations')}}
-- source(source name, table name)