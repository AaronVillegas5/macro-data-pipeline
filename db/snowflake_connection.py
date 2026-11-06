import os
from dotenv import load_dotenv

load_dotenv()


def get_snowflake_connection():
    try:
        import snowflake.connector
    except ImportError as e:
        raise RuntimeError(f"Snowflake connector not installed: {e}") from e

    snowflake_user = os.getenv("SNOWFLAKE_USER")
    snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")
    snowflake_account = os.getenv("SNOWFLAKE_ACCOUNT")

    return snowflake.connector.connect(
        user=snowflake_user,
        password=snowflake_password,
        account=snowflake_account,
        warehouse="COMPUTE_WH",
        database="MACRO_PIPELINE",
        schema="PUBLIC",
    )
