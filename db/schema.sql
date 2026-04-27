-- Locations (for weather or geographic grouping)
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name TEXT,
    country TEXT,
    region TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

-- Weather data
CREATE TABLE weather_observations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    observed_at TIMESTAMP NOT NULL,
    temperature_c DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    UNIQUE(location_id, observed_at)
);

-- Economic data (FRED)
CREATE TABLE economic_observations (
    id SERIAL PRIMARY KEY,
    series_id TEXT NOT NULL,
    series_name TEXT,
    observed_at TIMESTAMP NOT NULL,
    value DOUBLE PRECISION,
    UNIQUE(series_id, observed_at)
);
