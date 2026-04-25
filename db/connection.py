from sqlalchemy import create_engine 
from sqlalchemy.orm import declarative_base, sessionmaker 
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL, echo=False, future=True) 
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True) 
Base = declarative_base()   #Base class for API data

