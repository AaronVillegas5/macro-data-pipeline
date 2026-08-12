# 📊 Macro Data Pipeline

A Python-based data engineering project that collects, stores, and prepares multi-source time-series data for economic analysis and future forecasting.

The system integrates macroeconomic indicators, environmental data, and (in progress) retail sales data into a unified PostgreSQL database designed for analytical workflows. Weather observations are dual-written to Google BigQuery for scalable cloud analytics.

---

## 🚀 Features

- 📈 Ingests macroeconomic data from the FRED API
- 🌦 Collects historical weather data from Open-Meteo API
- 🏪 (In progress) integrates U.S. Census retail sales data
- 🗄 Stores structured time-series data in PostgreSQL and Snowflake (using robust MERGE INTO upserts) for advanced analytics
- 🔵 Dual-writes weather observations to **Google BigQuery** as a cloud analytics sink
- 📦 One-time historical migration script (`scripts/migrate_historical_weather.py`) using keyset pagination to backfill BigQuery `observations_v2` from PostgreSQL
- ☁️ Persists raw API JSON responses to AWS S3 for auditability and reprocessing
- 🔁 Implements idempotent upsert logic to prevent duplicates and safely handle missing time-series gaps
- 🧱 Modular service-based architecture for each data source
- ⚙️ Backfill system for historical data ingestion
- 🛠 **dbt Transformation Pipeline**: Modular Staging, Intermediate, and Mart models transforming 9M+ raw BigQuery observations into analytics-ready data marts
- 🤖 **CI/CD Data Testing**: Automated GitHub Actions pipeline that dynamically generates BigQuery profiles and runs `dbt run` & `dbt test` on all Pull Requests to guarantee data quality.

---

## 🧱 Tech Stack

- Python
- dbt (data build tool) & dbt-bigquery
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
git clone https://github.com/AaronVillegas5/macro-data-pipeline.git
cd macro-data-pipeline
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
pip install dbt-bigquery
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

**5. Run dbt Analytics Pipeline**
```bash
dbt run
dbt docs generate
dbt docs serve
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
                  ├──▶ Google BigQuery  (streaming & batch sinks)
                  │          │
                  │          ▼
                  │     dbt Transformations
                  │     (Staging ──▶ Intermediate ──▶ Marts)
                  │          │
                  │          ▼
                  │     BigQuery Marts (fct_monthly_macro_weather)
                  │
                  └──▶ Snowflake  (analytical warehouse)
```

Each data source is handled independently via modular service scripts. Weather and FRED economic observations are persisted to PostgreSQL and streamed/batched to **Google BigQuery**. dbt then transforms raw BigQuery datasets into analytics-ready fact and dimension tables.

---

## 🛠 dbt Transformations & Data Modeling

The dbt project organizes transformations into three distinct layers:

1. **Staging (`models/staging/`)**: Materialized as incremental models/views. Cleans raw BigQuery tables (`observations_v2`) and standardizes types & columns (`stg_weather_observations`, `stg_economic_observations`). Includes schema validation and custom bounds tests (e.g., `test_out_of_bounds.sql`).
2. **Intermediate (`models/intermediate/`)**: Materialized as views. Handles time-series aggregations and pivoting:
   - `int_monthly_weather_aggregates`: Calculates monthly average temperatures (`avg_monthly_temp_c`), total rainfall (`total_monthly_precipitation_mm`), and subzero freeze days.
   - `int_dry_spell`: Calculates the longest dry spell utilizing a reusable Jinja macro (`longest_streak.sql`) to solve gaps-and-islands problems dynamically.
   - `int_economic_indicators_pivoted`: Pivots long-format FRED series into wide columns (`cpi`, `unemployment_rate`, `gdp`).
3. **Marts (`models/marts/`)**: Materialized as physical tables.
   - `fct_monthly_macro_weather`: Joins monthly climate metrics with macroeconomic indicators for downstream dashboards and forecasting models.

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

**Google BigQuery**

| Dataset | Table | Description |
|---|---|---|
| `weather_data` | `observations_v2` | Raw streaming weather observations (clustered by `location_id`) |
| `economic_data` | `observations_v2` | Raw FRED economic indicators (partitioned by `MONTH(observed_at)`, clustered by `series_id`) |
| `dbt_dev` | `fct_monthly_macro_weather` | Combined analytical fact table generated by dbt |

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
- Historical temperature trends (`avg_temp_before_and_after_2000.sql`, `avg_temp_before_2000.sql`, `avg_temp_after_2000.sql`)
- Extreme weather event tracking (`hottest_years.sql`, `rainiest_years.sql`)
- Monthly and annual climate aggregations (`avg_temp_by_month.sql`, `avg_temp_by_year.sql`, `rain_by_year.sql`, `avg_rain_in_year.sql`)
- Database utility queries (`count_rows.sql`)

**`sql/bigquery/`** — BigQuery queries
- 30-day rolling average temperature per location (`avg_temp_rolling_30_days.sql`)
- Year-over-year temperature percentage change (`year_over_year_percentage.sql`)
- Average yearly difference (`avg_yearly_difference.sql`)
- Average yearly temperature (`avg_yearly_temp`)
- Longest subzero temperature streak (`longest_subzero_streak.sql`)
- Data deduplication (`deduplicate_data.sql`)
- Table creation and setup (`bigquery_create_weather_observations.sql`, `create_weather_table_v2.sql`)

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
├── macros/         # Reusable Jinja SQL macros (e.g., longest_streak.sql)
├── models/         # dbt transformation models (staging, intermediate, marts)
│   ├── staging/    # Cleansed raw BigQuery tables
│   ├── intermediate/# Pivoted economic data & weather aggregations
│   └── marts/       # Final analytical fact tables (fct_monthly_macro_weather)
├── tests/          # Custom dbt data tests (e.g., bounding tests, freshness checks)
├── scripts/        # Utility setup and migration scripts
│   ├── create_bq_economic_table.py
│   ├── migrate_historical_economic.py
│   └── migrate_historical_weather.py
├── services/       # Core business logic (S3 uploads, data parsing, dual-sink writes)
├── sql/
│   ├── postgres/   # PostgreSQL analytical queries
│   └── bigquery/   # BigQuery analytical queries
├── utilities/      # Helper functions (logging)
├── dbt_project.yml # dbt project configuration
├── Dockerfile      # Containerization configuration
└── main.py         # Application entry point


---

## 👨‍💻 Author

Aaron Villegas  
University of California, Irvine  
Applied & Computational Mathematics (Data Science)