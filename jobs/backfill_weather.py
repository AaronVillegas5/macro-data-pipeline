import requests
from datetime import date, timedelta, datetime
import time
from sqlalchemy.dialects.postgresql import insert
from db.connection import SessionLocal
from db.models import WeatherObservation
from services.s3_client import save_raw_response
from db.snowflake_connection import get_snowflake_connection
from services.snowflake_loader import load_weather_to_snowflake
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

SESSION = make_session()

def get_historical_weather(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": "temperature_2m,pressure_msl,relative_humidity_2m,windspeed_10m,precipitation",
        "timezone": "auto"
    }
    response = SESSION.get(url, params=params, timeout=(20, 30))
    response.raise_for_status()
    data = response.json()

    location_key = f"{lat}_{lon}"
    db = SessionLocal()
    try:
        save_raw_response("weather", location_key, data, db, start=start, end=end)
    finally:
        db.close()
    return data

def safe_get(arr, i):
    return arr[i] if arr and i < len(arr) else None

def parse_hourly(data, location_id):
    hourly = data.get("hourly", {})
    if not hourly:
        return []
    results = []
    for i in range(len(hourly["time"])):
        results.append({
            "location_id": location_id,
            "temperature_c": safe_get(hourly.get("temperature_2m"), i),
            "wind_speed": safe_get(hourly.get("windspeed_10m"), i),
            "pressure": safe_get(hourly.get("pressure_msl"), i),
            "humidity": safe_get(hourly.get("relative_humidity_2m"), i),
            "observed_at": datetime.fromisoformat(hourly["time"][i]),
            "precipitation": safe_get(hourly.get("precipitation"), i)
        })
    return results

def save_rows(rows):
    db = SessionLocal()
    try:
        if not rows:
            return
        stmt = insert(WeatherObservation).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["location_id", "observed_at"])
        db.execute(stmt)
        db.commit()
        print(f"Processed {len(rows)} rows (duplicates skipped automatically)")
    except Exception as e:
        db.rollback()
        print("Error:", e)
        raise
    finally:
        db.close()

def run(lat, lon, location_id, start_date, end_date):
    current = start_date
    today = date.today()
    end_date = min(end_date, today)

    conn = get_snowflake_connection()

    try:
        while current <= end_date:
            chunk_end = min(current + timedelta(days=19), end_date)
            print(f"Fetching {current} → {chunk_end}")
            try:
                data = get_historical_weather(lat, lon, str(current), str(chunk_end))
            except Exception as e:
                print(f"Skipping {current} → {chunk_end}: {e}")
                current = chunk_end + timedelta(days=1)
                continue

            rows = parse_hourly(data, location_id)

            try:                          # ← add this
                save_rows(rows)
            except Exception as e:
                print(f"DB save failed for {current} → {chunk_end}: {e}")
                current = chunk_end + timedelta(days=1)
                continue                  # ← keep going instead of dying

            snowflake_rows = [
                {
                    "latitude": lat,
                    "longitude": lon,
                    "observed_at": row["observed_at"],
                    "temperature": row["temperature_c"],
                    "precipitation": row["precipitation"] if row["precipitation"] is not None else 0.0
                }
                for row in rows
            ]
            load_weather_to_snowflake(conn, snowflake_rows)
            print(f"Sent {len(snowflake_rows)} to Snowflake")
            current = chunk_end + timedelta(days=1)
            time.sleep(0.2)

        print("Backfill complete!")

    except Exception as e:
        print(f"Backfill failed: {e}")   # ← catch top level errors too
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    run(
        lat=33.6405,
        lon=-117.6026,
        location_id=1,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 31)
    )