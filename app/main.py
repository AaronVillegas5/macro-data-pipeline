from fastapi import FastAPI
from fastapi import BackgroundTasks
import logging
app = FastAPI(
    title="Pi Macro Data Pipeline API",
    description="API for triggering data pipeline jobs and checking status"
)
# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)
#Root endpoint
@app.get("/")
def root():
    return {"status": "running"}

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "healthy 2"}

# Weather endpoint to trigger background job, with error handling and logging
@app.post("/jobs/weather")
def run_weather(background_tasks: BackgroundTasks):
    try:
        from jobs.fetch_weather import run
        background_tasks.add_task(run, 33.64, -117.60)
        logger.info("Weather job triggered")
        return {"status": "weather job started"}
    except Exception as e:
        logger.error(f"Failed to trigger weather job: {e}")
        return {"status": "error", "detail": str(e)}

# Trigger economic job
FRED_SERIES = {
    "CPIAUCSL": "Inflation (CPI)",
    "UNRATE": "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
    "GDP": "GDP",
    "UMCSENT": "Consumer Sentiment",
    "TOTALSA": "Total Vehicle Sales",
    "RSXFS": "Retail Sales"
}

@app.post("/jobs/economic")
def run_economic(background_tasks: BackgroundTasks):
    try:
        from jobs.fetch_economic import run
        for series_id, name in FRED_SERIES.items():
            background_tasks.add_task(run, series_id, name)
        logger.info("Economic job triggered")
        return {"status": "economic job started", "series_count": len(FRED_SERIES)}
    except Exception as e:
        logger.error(f"Failed to trigger economic job: {e}")
        return {"status": "error", "detail": str(e)}
