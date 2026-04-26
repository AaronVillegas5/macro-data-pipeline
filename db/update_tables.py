from sqlalchemy import text
from db.connection import engine

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE weather_observations
        ADD COLUMN humidity DOUBLE PRECISION
        ADD COLUMN pressure DOUBLE PRECISION
    """))
    conn.commit()