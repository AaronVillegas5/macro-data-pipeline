import os
import requests
from datetime import datetime
from utilities.logger import logger

# U.S. Census MARTS API Endpoint
CENSUS_API_URL = "https://api.census.gov/data/timeseries/econo/marts"

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
    "443": "Electronics and Appliance Stores"
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
        "get": "VAL,NAICS2012,NAICS2012_TTL",
        "for": "us:*",
        "time": f"from+{start_year}-01",
        "key": api_key
    }
    
    logger.info(f"Fetching retail data from {start_year}...")
    response = requests.get(CENSUS_API_URL, params=params)
    
    if response.status_code != 200:
        logger.error(f"Census API failed: {response.text}")
        return []

    data = response.json()
    
    # The first row contains the headers: ['VAL', 'NAICS2012', 'NAICS2012_TTL', 'time', 'us']
    headers = data[0]
    rows = data[1:]
    
    parsed_observations = []
    
    for row in rows:
        val, naics, naics_ttl, time_str, _ = row
        
        # We only care about our specific target sectors to save DB space
        if naics not in TARGET_NAICS:
            continue
            
        # Time comes in as 'YYYY-MM'
        try:
            observed_at = datetime.strptime(time_str, "%Y-%m")
            value = float(val) if val is not None else 0.0
            
            parsed_observations.append({
                "naics_code": naics,
                "category_name": TARGET_NAICS[naics],
                "value": value,
                "observed_at": observed_at
            })
        except ValueError as e:
            logger.warning(f"Error parsing row {row}: {e}")
            
    return parsed_observations
