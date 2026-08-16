import os

from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

from services.agent_tools import (
    check_data_freshness,
    compare_city_climates,
    get_climate_extremes,
    query_macro_weather_mart,
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
            compare_city_climates,
        ],
        temperature=0.2,
        system_instruction=(
            "You are an expert Macroeconomic & Climate Research Analyst. "
            "Always use your tools to query the official BigQuery data marts and database before answering. "
            "Provide executive summaries with key statistics and trends."
        ),
    )

    candidate_models = []
    if os.getenv("GEMINI_MODEL"):
        candidate_models.append(os.getenv("GEMINI_MODEL"))

    try:
        # Dynamically discover available models
        for m in client.models.list():
            if "gemini" in m.name.lower():
                # Some APIs return 'models/gemini...', we just want the 'gemini...' part
                model_id = m.name.split("/")[-1]
                candidate_models.append(model_id)
    except Exception:
        pass

    # Ensure we always have some models to try if discovery fails or returns empty
    if not candidate_models:
        candidate_models.extend(
            [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
            ]
        )

    # Deduplicate preserving order
    seen = set()
    candidate_models = [m for m in candidate_models if not (m in seen or seen.add(m))]
    candidate_models = [m for m in candidate_models if m]  # Ensure no empty strings

    if not candidate_models:
        candidate_models.extend(
            [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
            ]
        )

    print(f"DEBUG CANDIDATES: {candidate_models}")

    errors = {}
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            errors[model_name] = str(e)
            continue

    raise RuntimeError(f"Models attempted and their results: {errors}")


def generate_daily_executive_briefing() -> str:
    """Generates an executive briefing summarizing recent climate and macroeconomic trends."""
    prompt = (
        "Generate a concise 3-paragraph executive briefing on recent macroeconomic and climate trends. "
        "Use your tools to query the latest data from the data mart and highlight any key observations."
    )
    return ask_macro_agent(prompt)
