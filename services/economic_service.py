from api.fred_client import get_series
import datetime

def fetch_weather(series_id):
    data = get_series(series_id)

    # """ Obs look like
    # {
    #   "realtime_start": "2026-04-26",
    #   "realtime_end": "2026-04-26",
    #   "date": "1989-04-01",
    #   "value": "5612.463"
    # },
    # """

    observations = data.get("observations", {})
    if not observations:
        raise ValueError("No observations returned from FRED")
    rows = []

    for obs in observations:
        value = obs.get("value")
        if value == ".":
            continue
        rows.append({
            "series_id": series_id,
            "value": float(value),
            "observed_at": datetime.fromisoformat(obs["date"])
        })

    return rows