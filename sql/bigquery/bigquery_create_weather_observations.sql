-- =============================================================================
-- BigQuery DDL: weather_data.observations
--
-- Mirrors the PostgreSQL WeatherObservation model.
-- Run this once in the BigQuery console or via `bq query --use_legacy_sql=false`.
-- Replace <YOUR_PROJECT_ID> with your actual GCP project ID.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS `<YOUR_PROJECT_ID>.weather_data`
OPTIONS (
    description = "Weather observation data ingested from the pi-api pipeline",
    location    = "US"   -- change to "EU" or a regional location if preferred
);

CREATE TABLE IF NOT EXISTS `<YOUR_PROJECT_ID>.weather_data.observations` (
    -- Primary identifier (sourced from the PostgreSQL FK)
    location_id INT64 NOT NULL OPTIONS (description = "FK to locations table in PostgreSQL"),

    -- Measurements
    temperature_c FLOAT64 OPTIONS (description = "Air temperature in degrees Celsius"),
    wind_speed    FLOAT64 OPTIONS (description = "Wind speed (units match source API)"),
    pressure      FLOAT64 OPTIONS (description = "Atmospheric pressure"),
    humidity      FLOAT64 OPTIONS (description = "Relative humidity (%)"),
    precipitation FLOAT64 OPTIONS (description = "Precipitation amount"),

    -- Timestamps
    observed_at TIMESTAMP OPTIONS (description = "UTC timestamp of the weather observation"),
    created_at  TIMESTAMP OPTIONS (description = "Row insertion timestamp (set by pipeline)")
)
PARTITION BY DATE(observed_at)   -- partition pruning on time-range queries
CLUSTER BY location_id           -- clustering speeds up per-location filtering
OPTIONS (
    description              = "Streaming weather observations — dual-written from pi-api",
    require_partition_filter = FALSE
);
