
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
utilities/\

---

## 👨‍💻 Author

Aaron Villegas  
University of California, Irvine  
Applied & Computational Mathematics (Data Science)