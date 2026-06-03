# 📊 Macro Data Pipeline

A Python-based data engineering project that collects, stores, and prepares multi-source time-series data for economic analysis and future forecasting.

The system integrates macroeconomic indicators, environmental data, and (in progress) retail sales data into a unified PostgreSQL database designed for analytical workflows. Weather observations are dual-written to Google BigQuery for scalable cloud analytics.

---

## 🚀 Features

- 📈 Ingests macroeconomic data from the FRED API
- 🌦 Collects historical weather data from Open-Meteo API
- 🏪 (In progress) integrates U.S. Census retail sales data
- 🗄 Stores structured time-series data in PostgreSQL and Snowflake for advanced analytics
- 🔵 Dual-writes weather observations to **Google BigQuery** as a cloud analytics sink
- 📦 One-time historical migration script (`scripts/migrate_historical_weather.py`) to backfill BigQuery from existing PostgreSQL records
- ☁️ Persists raw API JSON responses to AWS S3 for auditability and reprocessing
- 🔁 Implements idempotent upsert logic to prevent duplicates
- 🧱 Modular service-based architecture for each data source
- ⚙️ Backfill system for historical data ingestion

---

## 🧱 Tech Stack

- Python
- PostgreSQL
- Google BigQuery
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
Copy `.env.example` to `.env` and fill in your credentials:
```env
FRED_API_KEY=your_fred_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/db
SNOWFLAKE_ACCOUNT=your_snowflake_account
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
BIGQUERY_PROJECT_ID=your_gcp_project_id
```

For BigQuery, authenticate via Application Default Credentials:
```bash
gcloud auth application-default login
```

**4. Run Database Migrations**
```bash
alembic upgrade head
```

---

## 🏗 Architecture

```
API Layer (FRED, Open-Meteo)
        │
        ▼
  Data Fetchers
        │
        ├──▶ Raw JSON  ──▶ AWS S3 (audit / reprocessing)
        │
        └──▶ Parsers / Cleaners
                  │
                  ├──▶ PostgreSQL  (upsert via SQLAlchemy)
                  ├──▶ Google BigQuery  (streaming insert — dual-sink)
                  └──▶ Snowflake  (analytical warehouse)
```

Each data source is handled independently via modular service scripts. Weather observations are written to **both PostgreSQL and BigQuery** in the same pipeline call via `save_weather()`, with each sink isolated in its own `try/except` block — a failure in one never blocks the other. Raw API responses are persisted to AWS S3 for auditability and reprocessing.
---

## 🗄 Database Schema

**PostgreSQL / Snowflake**

| Table | Description |
|---|---|
| `weather_observations` | Weather readings with upsert deduplication |
| `economic_observations` | FRED macroeconomic time-series |
| `locations` | Location reference table (lat/lon, region) |
| `retail_observations` | Planned: U.S. Census retail data |

All tables use uniqueness constraints and indexed timestamp columns for time-series deduplication.

**Google BigQuery** — `weather_data` dataset

| Table | Description |
|---|---|
| `observations` | Streaming weather sink, partitioned by `DATE(observed_at)`, clustered by `location_id` |

See [`sql/bigquery/bigquery_create_weather_observations.sql`](sql/bigquery/bigquery_create_weather_observations.sql) for the full DDL.

---

## 🧠 Goals

This project explores relationships between:

- Macroeconomic conditions (inflation, unemployment, GDP)
- Environmental factors (weather patterns)
- Consumer behavior (retail sales)

The goal is to build a foundation for real-world economic analysis and predictive modeling.

---

## 🔍 Analytical Queries

The `sql/` directory is organised by target database:

**`sql/postgres/`** — PostgreSQL queries
- Historical temperature trends (`avg_temp_before_and_after_2000.sql`)
- Extreme weather event tracking (`hottest_years.sql`, `rainiest_years.sql`)
- Monthly and annual climate aggregations

**`sql/bigquery/`** — BigQuery queries
- 30-day rolling average temperature per location (`avg_temp_rolling_30_days.sql`)

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
├── api/            # API clients for FRED and Open-Meteo
├── alembic/        # Database migration scripts
├── db/             # SQLAlchemy models and Snowflake connections
├── jobs/           # Automated scripts for fetching and backfilling data
├── scripts/        # One-off utility scripts
│   └── migrate_historical_weather.py  # Backfill PostgreSQL → BigQuery
├── services/       # Core business logic (S3 uploads, data parsing, dual-sink writes)
├── sql/
│   ├── postgres/   # PostgreSQL analytical queries
│   └── bigquery/   # BigQuery analytical queries
├── utilities/      # Helper functions (logging)
├── Dockerfile      # Containerization configuration
└── main.py         # Application entry point

---

## 👨‍💻 Author

Aaron Villegas  
University of California, Irvine  
Applied & Computational Mathematics (Data Science)