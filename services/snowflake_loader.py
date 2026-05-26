from db.snowflake_connection import get_snowflake_connection
from utilities.logger import logger
from datetime import datetime
def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    if isinstance(v, datetime):
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    return str(v)

def load_economic_to_snowflake(conn, rows):
    if not rows:
        return

    cursor = conn.cursor()

    try:
        batch_size = 500

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            values = ", ".join([
                f"({q(r['series_id'])}, {q(r['series_name'])}, {q(r['observed_at'])}, {q(r['value'])})"
                for r in batch
            ])

            sql = f"""
            MERGE INTO economic_observations AS target
            USING (
                SELECT * FROM VALUES {values}
                AS v(series_id, series_name, observed_at, value)
            ) AS source
            ON target.series_id = source.series_id
            AND target.observed_at = source.observed_at
            WHEN NOT MATCHED THEN
                INSERT (series_id, series_name, observed_at, value)
                VALUES (source.series_id, source.series_name, source.observed_at, source.value)
            """

            cursor.execute(sql)

        conn.commit()
        logger.info(f"Merged {len(rows)} economic rows to Snowflake")

    except Exception as e:
        conn.rollback()
        logger.error(f"Snowflake economic load failed: {e}")
        raise

    finally:
        cursor.close()


from db.snowflake_connection import get_snowflake_connection
from utilities.logger import logger


def load_weather_to_snowflake(conn, rows):
    if not rows:
        return

    batch_size = 500
    cursor = conn.cursor()

    try:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            start_date = batch[0]["observed_at"]
            end_date = batch[-1]["observed_at"]

            logger.info(f"Loading Snowflake batch: {start_date} → {end_date} ({len(batch)} rows)")

            current_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            values = ", ".join([
                f"({r['latitude']}, {r['longitude']}, "
                f"{q(r['observed_at'])}, "
                f"{r['temperature']}, "
                f"{r['precipitation'] if r.get('precipitation') is not None else 0.0}, "
                f"{q(current_ts)})"
                for r in batch
            ])

            sql = f"""
            MERGE INTO weather_observations AS target
            USING (
                SELECT * FROM VALUES {values}
                AS v(
                    latitude,
                    longitude,
                    observed_at,
                    temperature,
                    precipitation,
                    created_at
                )
            ) AS source
            ON target.latitude = source.latitude
            AND target.longitude = source.longitude
            AND target.observed_at = source.observed_at
            WHEN NOT MATCHED THEN
                INSERT (
                    latitude,
                    longitude,
                    observed_at,
                    temperature,
                    precipitation,
                    created_at
                )
                VALUES (
                    source.latitude,
                    source.longitude,
                    source.observed_at,
                    source.temperature,
                    source.precipitation,
                    source.created_at
                )
            """

            cursor.execute(sql)

        conn.commit()
        num_batches = (len(rows) + batch_size - 1) // batch_size

        logger.info(f"Merged {len(rows)} weather rows in {num_batches} batch(es)")

    except Exception as e:
        conn.rollback()
        logger.error(f"Snowflake load failed: {e}")
        raise

    finally:
        cursor.close()