from services.retail_service import fetch_retail_series
from services.save_retail import save_retail
from utilities.logger import logger

def run():
    logger.info("Starting Retail Sales ingestion job...")
    
    # We fetch data from 2015 to limit historical backfill scope for the API
    observations = fetch_retail_series(start_year="1992")
    
    if not observations:
        logger.warning("No retail data returned from Census API.")
        return
        
    logger.info(f"Fetched {len(observations)} retail data points. Saving to databases...")
    
    success_count = 0
    for obs in observations:
        try:
            save_retail(obs)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to save retail observation {obs.get('naics_code')}: {e}")
            
    logger.info(f"Retail Sales ingestion complete! Successfully saved {success_count} observations.")

if __name__ == "__main__":
    run()
