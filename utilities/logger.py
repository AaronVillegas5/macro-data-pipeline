import logging
import os
from datetime import datetime

LOG_DIR = "logs"
handlers = [logging.StreamHandler()]

try:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"app_{datetime.now().date()}.log")
    handlers.append(logging.FileHandler(log_file))
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=handlers,
)

logger = logging.getLogger("weather_app")
