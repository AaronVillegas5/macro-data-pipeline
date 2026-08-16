import os
from datetime import datetime

import requests

from utilities.logger import logger

# U.S. Census MARTS API Endpoint
CENSUS_API_URL = "https://api.census.gov/data/timeseries/eits/marts"

# Specific NAICS codes to track (as requested)
TARGET_NAICS = {
    "44W72": "Total Retail and Food Services Sales",
    "445": "Grocery Stores",
    "454": "E-commerce (Nonstore Retailers)",
    "441": "Motor Vehicle and Parts Dealers",
    "448": "Clothing and Clothing Accessories Stores",
    "722": "Food Services and Drinking Places",
    "447": "Gasoline Stations",
    "444": "Building Material and Garden Equipment and Supplies Dealers",
    "443": "Electronics and Appliance Stores",
}


def fetch_retail_series(start_year="1992"):
    """
    Fetches Monthly Retail Trade Survey (MARTS) data from the U.S. Census Bureau.
    Requires CENSUS_API_KEY in the environment.
    """
    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        logger.warning("CENSUS_API_KEY is not set. Requests may be heavily rate-limited.")

    params = {
        "get": "cell_value,data_type_code,category_code",
        "for": "us:*",
        "time": f"from {start_year}-01",
        "seasonally_adj": "yes",
        "key": api_key,
    }

    logger.info(f"Fetching retail data from {start_year}...")
    response = requests.get(CENSUS_API_URL, params=params)

    if response.status_code != 200:
        logger.error(f"Census API failed: {response.text}")
        return []

    data = response.json()

    # The first row contains the headers
    headers = data[0]
    rows = data[1:]

    parsed_observations = []

    for row in rows:
        # The variables returned are cell_value, data_type_code, category_code, time, and us (the geography)
        val, data_type, cat, time_str, _, _ = row

        # We only want "SM" (Sales - Monthly) to ignore percentage changes/estimates
        if data_type != "SM":
            continue

        # We only care about our specific target sectors to save DB space
        if cat not in TARGET_NAICS:
            continue

        # Time comes in as 'YYYY-MM'
        try:
            observed_at = datetime.strptime(time_str, "%Y-%m")
            value = float(val) if val is not None else 0.0

            parsed_observations.append(
                {
                    "naics_code": cat,
                    "category_name": TARGET_NAICS[cat],
                    "value": value,
                    "observed_at": observed_at,
                }
            )
        except ValueError as e:
            logger.warning(f"Error parsing row {row}: {e}")

    return parsed_observations
