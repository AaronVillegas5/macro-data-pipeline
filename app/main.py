from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from datetime import date
import logging

from app.routers.insights import router as insights_router

app = FastAPI(
    title="Pi Macro Data Pipeline API",
    description="API for triggering data pipeline jobs and checking status"
)

app.include_router(insights_router, prefix="/api/v1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Root endpoint
@app.get("/")
def root():
    return {"status": "running"}

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "healthy"}

# Weather job
@app.post("/jobs/weather")
def run_weather(background_tasks: BackgroundTasks):
    try:
        from jobs.fetch_weather import run
        background_tasks.add_task(run, 33.6405, -117.6026)
        logger.info("Weather job triggered")
        return {"status": "weather job started"}
    except Exception as e:
        logger.error(f"Failed to trigger weather job: {e}")
        return {"status": "error", "detail": str(e)}

# Economic job
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

# Backfill request model
class BackfillRequest(BaseModel):
    start_date: date
    end_date: date
    lat: float = 33.6405 #Default Irvine
    lon: float = -117.6026
    location_id: int = 1

# Backfill weather job with inputtable date range
@app.post("/jobs/backfill/weather")
def run_backfill_weather(request: BackfillRequest, background_tasks: BackgroundTasks):
    try:
        from jobs.backfill_weather import run
        background_tasks.add_task(
            run,
            request.lat,
            request.lon,
            request.location_id,
            request.start_date,
            request.end_date
        )
        logger.info(f"Backfill job triggered: {request.start_date} → {request.end_date}")
        return {
            "status": "backfill started",
            "start_date": str(request.start_date),
            "end_date": str(request.end_date),
            "lat": request.lat,
            "lon": request.lon
        }
    except Exception as e:
        logger.error(f"Failed to trigger backfill job: {e}")
        return {"status": "error", "detail": str(e)}