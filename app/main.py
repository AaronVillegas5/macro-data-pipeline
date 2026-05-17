from fastapi import FastAPI
from fastapi import BackgroundTasks

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/weather/run")
def run_weather(background_tasks: BackgroundTasks):
    from jobs.fetch_weather import run

    background_tasks.add_task(run, 33.64, -117.60)

    return {"status": "weather job started"}