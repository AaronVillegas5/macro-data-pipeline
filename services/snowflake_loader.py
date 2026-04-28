from db.snowflake_connection import get_snowflake_connection
from utilities.logger import logger

def load_economic_to_snowflake(rows):
    if not rows:
        return

    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        insert_sql = """
            INSERT INTO economic_observations 
            (series_id, series_name, observed_at, value)
            VALUES (%s, %s, %s, %s)
        """
        data = [(r["series_id"], r["series_name"], r["observed_at"], r["value"]) for r in rows]
        cursor.executemany(insert_sql, data)
        conn.commit()
        logger.info(f"Loaded {len(rows)} rows to Snowflake")

    except Exception as e:
        logger.error(f"Snowflake load failed: {e}")
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
        insert_sql = """
            INSERT INTO weather_observations
            (latitude, longitude, observed_at, temperature, precipitation)
            VALUES (%s, %s, %s, %s, %s)
        """
        data = [(
            r["latitude"],
            r["longitude"],
            r["observed_at"],
            r["temperature"],
            r["precipitation"]
        ) for r in rows]

        cursor.executemany(insert_sql, data)
        conn.commit()
        logger.info(f"Loaded {len(rows)} weather rows to Snowflake")

    except Exception as e:
        logger.error(f"Snowflake weather load failed: {e}")
        raise

    finally:
        cursor.close()
        conn.close()