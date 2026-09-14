import requests
import os

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def post_discord_alert(test_name, column_name, error_message):
    if not DISCORD_WEBHOOK_URL:
        return

    payload = {
        "content": f"🚨 **dbt Test Failure Detected** 🚨\n\n**Test:** {test_name}\n**Column:** {column_name}\n**Error:** {error_message}"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
