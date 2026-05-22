from services.economic_service import fetch_series
from db.models import EconomicObservation
from db.connection import SessionLocal
from utilities.logger import logger
from sqlalchemy.dialects.postgresql import insert
from services.snowflake_loader import load_economic_to_snowflake
from db.snowflake_connection import get_snowflake_connection

def run(series_id, name):
    logger.info(f"Fetching economic data for series_id={series_id}")
    db = SessionLocal()
    conn = get_snowflake_connection()
    try:
        rows = fetch_series(series_id)

        if not rows:
            logger.info("No data returned")
            return
        for row in rows:
            row["series_name"] = name

        stmt = insert(EconomicObservation).values(rows)

        # UPSERT
        stmt = stmt.on_conflict_do_update(
            index_elements=["series_id", "observed_at"],
            set_={
                "series_name": name,
                "value": stmt.excluded.value
            }
        )

        result = db.execute(stmt)
        db.commit()

        print(f"Processed {len(rows)} economic rows (duplicates skipped automatically)")
        load_economic_to_snowflake(conn, rows)

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()


if __name__ == "__main__":
    FRED_SERIES = {
        "CPIAUCSL": "Inflation (CPI)",
        "UNRATE": "Unemployment Rate",
        "FEDFUNDS": "Federal Funds Rate",
        "GDP": "GDP",
        "UMCSENT" : "Consumer Sentiment",
        "TOTALSA" : "Total Vehicle Sales",
        "RSXFS" : "Retail Sales"
    }
    for series_id, name in FRED_SERIES.items():
        run(series_id, name)