from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Any
from datetime import datetime, timedelta

from services.ai_agent import ask_macro_agent
from db.connection import SessionLocal

router = APIRouter(prefix="/insights", tags=["AI Insights"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    analysis: str


@router.post("/ask", response_model=QueryResponse)
def get_ai_insight(payload: QueryRequest):
    try:
        result = ask_macro_agent(payload.question)
        return QueryResponse(analysis=result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent error: {e!s}")


@router.get("/macro/summary")
def get_macro_summary(db: Session = Depends(get_db)):
    """Fetch latest pre-aggregated weather and macro observations from dbt mart."""
    query = text("SELECT * FROM rpt_macro_weather_dashboard ORDER BY observation_date DESC LIMIT 30")
    result = db.execute(query).fetchall()
    return [dict(row._mapping) for row in result]


@router.get("/health/freshness")
def check_freshness(db: Session = Depends(get_db)):
    """Checks if the latest data observation is less than 24 hours old."""
    query = text("""
        SELECT MAX(observed_at) as last_observation 
        FROM stg_weather_observations
    """)
    last_obs = db.execute(query).scalar()
    
    if not last_obs:
        return {"status": "NO_DATA"}
        
    is_stale = last_obs < (datetime.utcnow() - timedelta(hours=24))
    
    return {
        "status": "STALE" if is_stale else "HEALTHY",
        "last_observation": last_obs
    }
