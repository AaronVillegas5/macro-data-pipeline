from services.economic_service import fetch_series
from db.models import EconomicObservation
from db.connection import SessionLocal
from utilities.logger import logger
from sqlalchemy.dialects.postgresql import insert
from services.snowflake_loader import load_economic_to_snowflake
from db.snowflake_connection import get_snowflake_connection

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

def fetch_and_save_series(db, conn, series_id, name):
    logger.info(f"Fetching economic data for series_id={series_id} ({name})")
    rows = fetch_series(series_id)

    if not rows:
        logger.info(f"No data returned for {series_id}")
        return

    for row in rows:
        row["series_name"] = name

    stmt = insert(EconomicObservation).values(rows)

    # UPSERT into PostgreSQL
    stmt = stmt.on_conflict_do_update(
        index_elements=["series_id", "observed_at"],
        set_={
            "series_name": name,
            "value": stmt.excluded.value
        }
    )

    db.execute(stmt)
    db.commit()
    logger.info(f"Processed {len(rows)} economic rows for {series_id} in PostgreSQL")

    # Load to Snowflake with error isolation
    if conn:
        try:
            load_economic_to_snowflake(conn, rows)
        except Exception as e:
            logger.warning(f"Snowflake economic load failed for {series_id}: {e}")

def run(series_id=None, name=None):
    db = SessionLocal()
    conn = None
    try:
        try:
            conn = get_snowflake_connection()
        except Exception as e:
            logger.warning(f"Could not connect to Snowflake: {e}")

        if series_id and name:
            fetch_and_save_series(db, conn, series_id, name)
        else:
            for s_id, s_name in FRED_SERIES.items():
                try:
                    fetch_and_save_series(db, conn, s_id, s_name)
                except Exception as e:
                    logger.error(f"Failed processing series {s_id}: {e}")

    except Exception as e:
        logger.exception(f"Error during economic data processing: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
