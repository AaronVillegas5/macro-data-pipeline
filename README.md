# 📊 Macro Data Pipeline

A Python-based data engineering project that collects, stores, and prepares multi-source time-series data for economic analysis and future forecasting.

The system integrates macroeconomic indicators, environmental data, and (in progress) retail sales data into a unified PostgreSQL database designed for analytical workflows.

---

## 🚀 Features

- 📈 Ingests macroeconomic data from the FRED API
- 🌦 Collects historical weather data from Open-Meteo API
- 🏪 (In progress) integrates U.S. Census retail sales data
- 🗄 Stores structured time-series data in PostgreSQL and Snowflake for advanced analytics 
- ☁️ Persists raw API JSON responses to AWS S3 for auditability and reprocessing
- 🔁 Implements idempotent upsert logic to prevent duplicates
- 🧱 Modular service-based architecture for each data source
- ⚙️ Backfill system for historical data ingestion

---

## 🧱 Tech Stack

- Python
- PostgreSQL
- Snowflake
- AWS S3
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

## 🛠 Getting Started

**1. Clone the repository**
```bash
git clone [https://github.com/AaronVillegas5/macro-data-pipeline.git](https://github.com/AaronVillegas5/macro-data-pipeline.git)
cd macro-data-pipeline
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
```

**3. Environment Variables**
Create a `.env` file in the root directory and add your necessary credentials:
```env
FRED_API_KEY=your_fred_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/db
SNOWFLAKE_ACCOUNT=your_snowflake_account
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

**4. Run Database Migrations**
```bash
alembic upgrade head
```

---

## 🏗 Architecture

API Layer (FRED, Open-Meteo) → Data Fetchers → Raw JSON Storage (AWS S3)
                                           ↳ Parsers → Cleaned Data → PostgreSQL & Snowflake

Each data source is handled independently via modular service scripts. To ensure data integrity, raw API responses are persisted directly to AWS S3 for auditability and potential reprocessing. Simultaneously, the data is parsed, cleaned, and loaded into both PostgreSQL and Snowflake, where it is optimized for time-series analysis and dashboarding.
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

## 🔍 Analytical Queries

The `sql/` directory contains pre-built analytical queries demonstrating how the structured data can be leveraged for insights. Examples include:

- Historical temperature trends (`avg_temp_before_and_after_2000.sql`)
- Extreme weather event tracking (`hottest_years.sql`, `rainiest_years.sql`)
- Monthly and annual climate aggregations

---

## 🔮 Future Work

- Add U.S. Census retail sales integration
- Build Jupyter-based analysis notebooks
- Perform correlation and lag analysis (CPI vs retail spending)
- Add forecasting models (ARIMA / XGBoost)
- Deploy dashboard (Streamlit / Plotly Dash)

---

## 📁 Project Structure

```text
├── api/          # API clients for FRED and Open-Meteo
├── alembic/      # Database migration scripts
├── db/           # SQLAlchemy models and Snowflake connections
├── jobs/         # Automated scripts for fetching and backfilling data
├── services/     # Core business logic (S3 uploads, data parsing)
├── sql/          # Analytical SQL queries for data exploration
├── utilities/    # Helper functions (logging)
├── Dockerfile    # Containerization configuration
└── main.py       # Application entry point

---

## 👨‍💻 Author

Aaron Villegas  
University of California, Irvine  
Applied & Computational Mathematics (Data Science)