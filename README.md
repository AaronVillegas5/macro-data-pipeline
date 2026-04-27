# 📊 Macro Data Pipeline

A Python-based data engineering project that collects, stores, and prepares multi-source time-series data for economic analysis and future forecasting.

The system integrates macroeconomic indicators, environmental data, and (in progress) retail sales data into a unified PostgreSQL database designed for analytical workflows.

---

## 🚀 Features

- 📈 Ingests macroeconomic data from the FRED API
- 🌦 Collects historical weather data from Open-Meteo API
- 🏪 (In progress) integrates U.S. Census retail sales data
- 🗄 Stores structured time-series data in PostgreSQL
- 🔁 Implements idempotent upsert logic to prevent duplicates
- 🧱 Modular service-based architecture for each data source
- ⚙️ Backfill system for historical data ingestion

---

## 🧱 Tech Stack

- Python
- PostgreSQL
- SQLAlchemy
- Alembic
- REST APIs
- Pandas (for analysis layer)

---

## 📊 Data Sources

- Federal Reserve Economic Data (FRED)
- Open-Meteo Weather API
- U.S. Census Bureau (planned: retail trade data)

---

## 🏗 Architecture
API Layer → Data Fetchers → Parsers → Database Layer → Analytics (future) \

Each data source is handled independently via service modules and normalized into a unified schema.

---

## 🗄 Database Schema

Core tables:

- `economic_observations`
- `weather_observations`
- `retail_observations` (planned)
- `locations`

All tables are optimized for time-series analysis with uniqueness constraints for deduplication.

---

## 🧠 Goals

This project explores relationships between:

- Macroeconomic conditions (inflation, unemployment, GDP)
- Environmental factors (weather patterns)
- Consumer behavior (retail sales)

The goal is to build a foundation for real-world economic analysis and predictive modeling.

---

## 🔮 Future Work

- Add U.S. Census retail sales integration
- Build Jupyter-based analysis notebooks
- Perform correlation and lag analysis (CPI vs retail spending)
- Add forecasting models (ARIMA / XGBoost)
- Deploy dashboard (Streamlit / Plotly Dash)

---

## 📁 Project Structure
api/\
services/\
db/\
jobs/\
alembic/ \
utilities/

---

## 👨‍💻 Author

Aaron Villegas  
University of California, Irvine  
Applied & Computational Mathematics (Data Science)