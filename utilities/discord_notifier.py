import logging
import os
import requests

logger = logging.getLogger(__name__)


def post_discord_alert(test_name: str, column_name: str, error_message: str, timeout: int = 10) -> None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    payload = {
        "content": (
            f"🚨 **dbt Test Failure Detected** 🚨\n\n"
            f"**Test:** {test_name}\n"
            f"**Column:** {column_name}\n"
            f"**Error:** {error_message}"
        )
    }
    try:
        requests.post(webhook_url, json=payload, timeout=timeout)
    except Exception as exc:
        logger.warning(f"Failed to post Discord alert: {exc}")
