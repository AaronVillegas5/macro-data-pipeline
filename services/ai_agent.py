import os
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from services.agent_tools import (
    query_macro_weather_mart,
    check_data_freshness,
    get_climate_extremes,
    compare_city_climates
)

def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables or .env")
    return genai.Client(api_key=api_key)

def ask_macro_agent(user_prompt: str) -> str:
    """Invokes the AI agent with tool-calling access to BigQuery data marts."""
    client = get_genai_client()

    config = types.GenerateContentConfig(
        tools=[
            query_macro_weather_mart,
            check_data_freshness,
            get_climate_extremes,
            compare_city_climates
        ],
        temperature=0.2,
        system_instruction=(
            "You are an expert Macroeconomic & Climate Research Analyst. "
            "Always use your tools to query the official BigQuery data marts and database before answering. "
            "Provide executive summaries with key statistics and trends."
        )
    )

    candidate_models = [
        os.getenv("GEMINI_MODEL"),
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3-flash",
        "gemini-2.5-flash-lite"
    ]
    candidate_models = [m for m in candidate_models if m]

    last_error = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            transient_or_missing = [
                "404", "503", "429",
                "not found", "no longer available",
                "unavailable", "high demand", "resource_exhausted"
            ]
            if any(term in error_msg for term in transient_or_missing):
                continue
            raise e

    raise RuntimeError(f"All candidate Gemini models failed: {last_error}")

def generate_daily_executive_briefing() -> str:
    """Generates an executive briefing summarizing recent climate and macroeconomic trends."""
    prompt = (
        "Generate a concise 3-paragraph executive briefing on recent macroeconomic and climate trends. "
        "Use your tools to query the latest data from the data mart and highlight any key observations."
    )
    return ask_macro_agent(prompt)
