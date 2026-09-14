import os
from pathlib import Path
import logging
import csv
from datetime import date
from typing import Optional, Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from app.routers.insights import router as insights_router

app = FastAPI(
    title="Pi Macro Data Pipeline API",
    description="API for triggering data pipeline jobs and checking status",
)

app.include_router(insights_router, prefix="/api/v1")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def get_fred_series() -> Dict[str, str]:
    """Loads FRED series configuration from a CSV file."""
    series = {}
    csv_path = os.getenv("FRED_SERIES_CSV_PATH")
    if not csv_path or not os.path.exists(csv_path):
        candidate_path = Path(__file__).resolve().parent.parent / "fred_series.csv"
        csv_path = str(candidate_path) if candidate_path.exists() else "/srv/projects/pi-api/fred_series.csv"
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    series[row[0].strip()] = row[1].strip()
    except Exception as e:
        logger.error(f"Failed to load FRED configuration: {e}")
    return series

# ==Pydantic Models ==
class JobStatusResponse(BaseModel):
    status: str
    detail: Optional[str] = None
    series_count: Optional[int] = None


class BackfillResponse(BaseModel):
    status: str
    start_date: str
    end_date: str
    lat: float
    lon: float


# Backfill request model
class BackfillRequest(BaseModel):
    start_date: date
    end_date: date
    lat: float = Field(default=33.6405, ge=-90, le=90)
    lon: float = Field(default=-117.6026, ge=-180, le=180)
    location_id: int = 1

    @model_validator(mode='after')
    def check_dates(self) -> 'BackfillRequest':
        if self.start_date > self.end_date:
            raise ValueError('start_date must be before end_date')
        return self


class WeatherJobRequest(BaseModel):
    lat: float = Field(default=33.6405, ge=-90, le=90)
    lon: float = Field(default=-117.6026, ge=-180, le=180)


@app.get("/", summary="Root status endpoint")
def root():
    """Returns the current operational status of the API."""
    return {"status": "running"}


@app.get("/health", summary="Health check endpoint")
def health():
    """Checks the health of the API."""
    return {"status": "healthy"}


# Weather job
@app.post("/jobs/weather", response_model=JobStatusResponse, summary="Trigger a weather data fetch job")
def run_weather(request: WeatherJobRequest, background_tasks: BackgroundTasks):
    """
    Triggers a background job to fetch weather data for the specified coordinates.

    Args:
        request (WeatherJobRequest): The location coordinates (lat, lon).
        background_tasks (BackgroundTasks): FastAPI background task handler.

    Returns:
        JobStatusResponse: A summary status of the initiated job.

    Raises:
        HTTPException: If the job cannot be triggered.
    """
    try:
        from jobs.fetch_weather import run

        background_tasks.add_task(run, request.lat, request.lon)
        logger.info("Weather job triggered")
        return {"status": "weather job started"}
    except Exception as e:
        logger.error(f"Failed to trigger weather job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger weather job: {str(e)}"
        )


# Economic job
@app.post("/jobs/economic", response_model=JobStatusResponse, summary="Trigger economic data fetch jobs")
def run_economic(background_tasks: BackgroundTasks):
    """
    Triggers background jobs to fetch various economic indicators from FRED based on config.

    Args:
        background_tasks (BackgroundTasks): FastAPI background task handler.

    Returns:
        JobStatusResponse: A summary status including the number of series fetched.

    Raises:
        HTTPException: If the job cannot be triggered.
    """
    fred_series = get_fred_series()
    if not fred_series:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No FRED series configuration loaded"
        )

    try:
        from jobs.fetch_economic import run

        for series_id, name in fred_series.items():
            background_tasks.add_task(run, series_id, name)
        logger.info("Economic job triggered")
        return {"status": "economic job started", "series_count": len(fred_series)}
    except Exception as e:
        logger.error(f"Failed to trigger economic job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger economic job: {str(e)}"
        )


# Backfill weather job with inputtable date range
@app.post("/jobs/backfill/weather", response_model=BackfillResponse, summary="Trigger weather backfill")
def run_backfill_weather(request: BackfillRequest, background_tasks: BackgroundTasks):
    """
    Triggers a background job to backfill weather data for a specific date range and location.

    Args:
        request (BackfillRequest): The location and date range for the backfill.
        background_tasks (BackgroundTasks): FastAPI background task handler.

    Returns:
        BackfillResponse: Confirmation of the requested backfill parameters.

    Raises:
        HTTPException: If the job cannot be triggered.
    """
    try:
        from jobs.backfill_weather import run

        background_tasks.add_task(
            run,
            request.lat,
            request.lon,
            request.location_id,
            request.start_date,
            request.end_date,
        )
        logger.info(f"Backfill job triggered: {request.start_date} → {request.end_date}")
        return {
            "status": "backfill started",
            "start_date": str(request.start_date),
            "end_date": str(request.end_date),
            "lat": request.lat,
            "lon": request.lon,
        }
    except Exception as e:
        logger.error(f"Failed to trigger backfill job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger backfill job: {str(e)}"
        )
