from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_agent import ask_macro_agent

router = APIRouter(prefix="/insights", tags=["AI Insights"])


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
