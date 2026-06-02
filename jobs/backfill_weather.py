import requests
from datetime import date, timedelta, datetime
import time
from sqlalchemy.dialects.postgresql import insert
from db.connection import SessionLocal
from db.models import WeatherObservation, Location
from services.s3_client import save_raw_response
from db.snowflake_connection import get_snowflake_connection
from services.snowflake_loader import load_weather_pipeline
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy import func


# ---------------------------
# HTTP session with retries
# ---------------------------
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


# ---------------------------
# DB helpers
# ---------------------------
def get_last_date(db, location_id):
    return (
        db.query(func.max(WeatherObservation.observed_at))
        .filter(WeatherObservation.location_id == location_id)
        .scalar()
    )


def save_rows(rows):
    db = SessionLocal()
    try:
        if not rows:
            return

        stmt = insert(WeatherObservation).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["location_id", "observed_at"]
        )

        db.execute(stmt)
        db.commit()

        print(f"Processed {len(rows)} rows")

    except Exception as e:
        db.rollback()
        print("Postgres error:", e)
        raise
    finally:
        db.close()


# ---------------------------
# API fetch + parse
# ---------------------------
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

    db = SessionLocal()
    try:
        save_raw_response(
            "weather",
            f"{lat}_{lon}",
            data,
            db,
            start=start,
            end=end
        )
    finally:
        db.close()

    return data


def safe_get(arr, i):
    return arr[i] if arr and i < len(arr) else None


def parse_hourly(data, location_id, lat, lon):
    hourly = data.get("hourly", {})
    if not hourly:
        return []

    results = []

    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m")
    wind = hourly.get("windspeed_10m")
    pressure = hourly.get("pressure_msl")
    humidity = hourly.get("relative_humidity_2m")
    precip = hourly.get("precipitation")

    for i in range(len(times)):
        results.append({
            "location_id": location_id,
            "temperature_c": safe_get(temps, i),
            "wind_speed": safe_get(wind, i),
            "pressure": safe_get(pressure, i),
            "humidity": safe_get(humidity, i),
            "observed_at": datetime.fromisoformat(times[i]),
            "precipitation": safe_get(precip, i),
        })

    return results


# ---------------------------
# CORE RUN (NO FLUSH HERE)
# ---------------------------
def run(lat, lon, location_id, start_date, end_date, location_name=None):
    current = start_date
    end_date = min(end_date, date.today())

    buffer = []

    while current <= end_date:
        chunk_end = min(current + timedelta(days=19), end_date)

        print(f"Fetching {current} → {chunk_end} for {location_name}")

        try:
            data = get_historical_weather(lat, lon, str(current), str(chunk_end))
        except Exception as e:
            print(f"Skipping chunk: {e}")
            current = chunk_end + timedelta(days=1)
            continue

        rows = parse_hourly(data, location_id, lat, lon)

        if not rows:
            current = chunk_end + timedelta(days=1)
            continue

        # Postgres insert (optional but kept)
        try:
            save_rows(rows)
        except Exception as e:
            print(f"Postgres failed: {e}")
            current = chunk_end + timedelta(days=1)
            continue

        # ---------------------------
        # BUFFER FOR SNOWFLAKE
        # ---------------------------
        buffer.extend([
            {
                "latitude": lat,
                "longitude": lon,
                "observed_at": r["observed_at"],
                "temperature": r.get("temperature_c"),
                "precipitation": r.get("precipitation", 0.0),
            }
            for r in rows
        ])

        current = chunk_end + timedelta(days=1)
        time.sleep(0.2)

    # return buffer so caller controls flushing
    return buffer


# ---------------------------
# MAIN
# ---------------------------
if __name__ == "__main__":
    db = SessionLocal()
    conn = get_snowflake_connection()

    if not conn:
        print("WARNING: Snowflake connection failed. Running in Postgres-only mode.")

    try:
        locations = db.query(Location).filter(
            Location.name != "Rancho Santa Margarita",
            Location.name != "Big Bear Lake",
            Location.name != "San Diego"
        ).all()

        for loc in locations:
            last_date = get_last_date(db, loc.id)
            start = last_date.date() + timedelta(days=1) if last_date else date(1950, 1, 1)
            end = date.today() - timedelta(days=1)

            print(f"\n=== {loc.name} ===")
            buffer = run(
                lat=loc.latitude,
                lon=loc.longitude,
                location_id=loc.id,
                start_date=start,
                end_date=end,
                location_name=loc.name
            )

            # ---------------------------
            # SINGLE FLUSH PER LOCATION
            # ---------------------------
            if buffer:
                if conn:
                    print(f"Flushing {len(buffer)} rows to Snowflake for {loc.name}")
                    try:
                        load_weather_pipeline(conn, buffer)
                    except Exception as e:
                        print(f"Snowflake failed for {loc.name}, but Postgres succeeded. Error: {e}")
                else:
                    print(f"Skipping Snowflake flush for {loc.name} (No connection).")
                
                del buffer
                import gc
                gc.collect()

    finally:
        if conn:
            conn.close()
        db.close()
    print("Backfill complete!")