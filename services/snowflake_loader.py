from db.snowflake_connection import get_snowflake_connection
from utilities.logger import logger

def load_economic_to_snowflake(rows):
    if not rows:
        return

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        for r in rows:
            cursor.execute("""
                MERGE INTO economic_observations AS target
                USING (
                    SELECT %s AS series_id, %s AS series_name,
                           %s AS observed_at, %s AS value
                ) AS source
                ON target.series_id = source.series_id
                AND target.observed_at = source.observed_at
                WHEN NOT MATCHED THEN
                    INSERT (series_id, series_name, observed_at, value)
                    VALUES (source.series_id, source.series_name,
                            source.observed_at, source.value)
            """, (r["series_id"], r["series_name"], r["observed_at"], r["value"]))

        conn.commit()
        logger.info(f"Merged {len(rows)} economic rows to Snowflake")

    except Exception as e:
        logger.error(f"Snowflake economic load failed: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


def load_weather_to_snowflake(rows):
    if not rows:
        return

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        for r in rows:
            cursor.execute("""
                MERGE INTO weather_observations AS target
                USING (
                    SELECT %s AS latitude, %s AS longitude,
                           %s AS observed_at, %s AS temperature,
                           %s AS precipitation
                ) AS source
                ON target.latitude = source.latitude
                AND target.longitude = source.longitude
                AND target.observed_at = source.observed_at
                WHEN NOT MATCHED THEN
                    INSERT (latitude, longitude, observed_at,
                            temperature, precipitation)
                    VALUES (source.latitude, source.longitude,
                            source.observed_at, source.temperature,
                            source.precipitation)
            """, (r["latitude"], r["longitude"], r["observed_at"],
                  r["temperature"], r["precipitation"]))

        conn.commit()
        logger.info(f"Merged {len(rows)} weather rows to Snowflake")

    except Exception as e:
        logger.error(f"Snowflake weather load failed: {e}")
        raise

    finally:
        cursor.close()
        conn.close()