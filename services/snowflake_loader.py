from datetime import datetime

from utilities.logger import logger


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    if isinstance(v, datetime):
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    return str(v)


def load_economic_to_snowflake(conn, rows):
    """
    Loads economic observation data into Snowflake using a MERGE INTO upsert pattern.

    Data Validation & Edge Cases:
    - Verifies `rows` is not empty prior to execution to prevent empty queries.
    - Safely formats data using the `q()` helper which properly escapes strings and handles NULL values,
      preventing SQL injection or parsing errors on null data points.
    - Time-Series Gaps: Batch processing inherently supports sparse data sets since missing dates are simply omitted.

    Cloud Destination (Snowflake):
    - Uses `MERGE INTO economic_observations` matching on the composite key (series_id, observed_at).
    - Idempotency is guaranteed by only performing an INSERT `WHEN NOT MATCHED`. This prevents duplicates
      if the pipeline is rerun over existing historical periods.
    """
    if not rows:
        return

    cursor = conn.cursor()

    try:
        batch_size = 500

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]

            values = ", ".join(
                [
                    f"({q(r['series_id'])}, {q(r['series_name'])}, {q(r['observed_at'])}, {q(r['value'])})"
                    for r in batch
                ]
            )

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


def load_weather_to_snowflake(conn, rows):
    if not rows:
        return
    created_at = datetime.utcnow()

    cursor = conn.cursor()

    try:
        batch_size = 50000  # bigger batches = fewer round trips

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]

            logger.info(f"Staging batch {i}-{i + len(batch)} ({len(batch)} rows)")
            print("INSERTING INTO SNOWFLAKE:", len(batch))
            print(batch[0])

            cursor.executemany(
                """
            INSERT INTO weather_observations_stage (
                latitude,
                longitude,
                observed_at,
                temperature,
                precipitation,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
                [
                    (
                        r["latitude"],
                        r["longitude"],
                        r["observed_at"],
                        r.get("temperature"),
                        r.get("precipitation", 0.0),
                        created_at,
                    )
                    for r in batch
                ],
            )
        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Staging load failed: {e}")
        raise

    finally:
        cursor.close()


def merge_weather(conn):
    """
    Executes the MERGE INTO logic to upsert staged weather data into the final Snowflake table.

    Data Validation & Edge Cases:
    - Expected nulls in mutable columns (e.g., precipitation, temperature) are handled natively
      during the staging phase `load_weather_to_snowflake()`.

    Cloud Destination (Snowflake):
    - Assumes data has been pre-loaded into `weather_observations_stage`.
    - Conflicts on (latitude, longitude, observed_at) are skipped (`WHEN NOT MATCHED THEN INSERT`).
    - This approach provides idempotent inserts, meaning overlapping time-series data won't corrupt the warehouse.
    """
    cursor = conn.cursor()

    try:
        cursor.execute("""
        MERGE INTO weather_observations t
        USING (
            SELECT *
            FROM weather_observations_stage
        ) s
        ON t.latitude = s.latitude
        AND t.longitude = s.longitude
        AND t.observed_at = s.observed_at
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
                s.latitude,
                s.longitude,
                s.observed_at,
                s.temperature,
                s.precipitation,
                s.created_at
            )
        """)

        conn.commit()

    finally:
        cursor.close()


def clear_stage(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE weather_observations_stage")
        conn.commit()
    finally:
        cursor.close()


def load_weather_pipeline(conn, rows):
    load_weather_to_snowflake(conn, rows)
    try:
        merge_weather(conn)
    except Exception:
        logger.error("Merge failed")
        raise
    finally:
        clear_stage(conn)
