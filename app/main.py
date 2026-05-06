from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/weather/run")
def run_weather():
    from jobs.fetch_weather import run
    run(33.64, -117.60)
    return {"status": "weather job executed"}