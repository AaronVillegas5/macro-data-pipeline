import requests
from datetime import date, timedelta, datetime
from sqlalchemy.dialects.postgresql import insert
from db.connection import SessionLocal
from db.models import WeatherObservation
from services.s3_client import save_raw_response


# -------------------------------
# 1. API CALL
# -------------------------------
def get_historical_weather(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": "temperature_2m,pressure_msl,relative_humidity_2m,windspeed_10m",
        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    data = response.json()

    #Saving to S3 bucket
    location_key = f"{lat}_{lon}"
    db = SessionLocal()
    try:
        save_raw_response("weather", location_key, data, db)
    finally:
        db.close()
    return data


# -------------------------------
# 2. PARSE DATA
# -------------------------------
def parse_hourly(data, location_id):
    hourly = data.get("hourly", {})

    if not hourly:
        return []

    results = []

    for i in range(len(hourly["time"])):
        results.append({
            "location_id": location_id,
            "temperature_c": hourly["temperature_2m"][i],
            "wind_speed": hourly["windspeed_10m"][i],
            "pressure": hourly["pressure_msl"][i],
            "humidity": hourly["relative_humidity_2m"][i],
            "observed_at": datetime.fromisoformat(hourly["time"][i])
        })

    return results


# -------------------------------
# 3. SAVE (skip duplicates)
# -------------------------------
def save_rows(rows):
    db = SessionLocal()

    try:
        if not rows:
            return
        # Create bulk insert statement
        stmt = insert(WeatherObservation).values(rows)

        # UPSERT
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["location_id", "observed_at"]
        )

        result = db.execute(stmt)
        db.commit()

        print(f"Processed {len(rows)} rows (duplicates skipped automatically)")
    except Exception as e:
        db.rollback()
        print("Error:", e)
        raise  

    finally:
        db.close()

# -------------------------------
# 4. MAIN BACKFILL LOOP
# -------------------------------
def run(lat, lon, location_id, start_date, end_date):
    current = start_date
    today = date.today()
    end_date = min(end_date, today)

    while current <= end_date:
        chunk_end = min(current + timedelta(days=7), end_date)

        print(f"Fetching {current} → {chunk_end}")
        try:
            data = get_historical_weather(
                lat,
                lon,
                str(current),
                str(chunk_end)
            )
        except Exception as e:
            print(f"Skipping {current} → {chunk_end}: {e}")
            current = chunk_end + timedelta(days=1)
            continue

        rows = parse_hourly(data, location_id)
        save_rows(rows)

        current = chunk_end + timedelta(days=1)

    print("Backfill complete!")


if __name__ == "__main__":
    run(
        lat=33.6405,
        lon=-117.6026,
        location_id=1,
        start_date=date(2024, 1, 1),
        end_date=date(2026, 4, 26)
    )