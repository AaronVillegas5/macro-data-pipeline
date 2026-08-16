import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL")
print("Connecting to:", DATABASE_URL)


engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM weather_observations ORDER BY observed_at DESC LIMIT 5"))

    for row in result:
        print(row)
    print("Connected successfully!")
