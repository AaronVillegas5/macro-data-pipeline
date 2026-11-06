from db.snowflake_connection import get_snowflake_connection
from services.economic_service import fetch_series
from services.save_economic import save_economic
from services.snowflake_loader import load_economic_to_snowflake
from utilities.logger import logger

FRED_SERIES = {
    # Inflation
    "CPIAUCSL": "Inflation (CPI)",
    "CPILFESL": "Core CPI",
    "PCEPI": "PCE Inflation",
    # Labor
    "UNRATE": "Unemployment Rate",
    "PAYEMS": "Nonfarm Payrolls",
    "ICSA": "Initial Claims",
    # Rates
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10Y Treasury",
    "T10Y2Y": "Yield Curve Spread",
    # Activity
    "INDPRO": "Industrial Production",
    "HOUST": "Housing Starts",
    # Demand
    "PCE": "Personal Consumption",
    "CSUSHPISA": "Home Price Index",
    "DCOILWTICO": "Crude Oil Price",
    "JTSJOL": "Job Openings",
}


def fetch_and_save_series(conn, series_id, name):
    logger.info(f"Fetching economic data for series_id={series_id} ({name})")
    rows = fetch_series(series_id)

    if not rows:
        logger.info(f"No data returned for {series_id}")
        return

    for row in rows:
        row["series_name"] = name

    # Dual-sink to PostgreSQL and BigQuery with error isolation
    save_economic(rows)
    logger.info(f"Processed {len(rows)} economic rows for {series_id}")

    # Load to Snowflake with error isolation if connected
    if conn:
        try:
            load_economic_to_snowflake(conn, rows)
        except Exception as e:
            logger.warning(f"Snowflake economic load failed for {series_id}: {e}")


def run(series_id=None, name=None):
    conn = None
    try:
        try:
            conn = get_snowflake_connection()
        except Exception as e:
            logger.warning(f"Could not connect to Snowflake: {e}")

        if series_id and name:
            fetch_and_save_series(conn, series_id, name)
        else:
            for s_id, s_name in FRED_SERIES.items():
                try:
                    fetch_and_save_series(conn, s_id, s_name)
                except Exception as e:
                    logger.error(f"Failed processing series {s_id}: {e}")

    except Exception as e:
        logger.exception(f"Error during economic data processing: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    run()
