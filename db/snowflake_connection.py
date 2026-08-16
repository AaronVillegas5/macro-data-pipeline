import os

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()
snowflake_user = os.getenv("SNOWFLAKE_USER")
snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")
snowflake_account = os.getenv("SNOWFLAKE_ACCOUNT")


def get_snowflake_connection():
    return snowflake.connector.connect(
        user=snowflake_user,
        password=snowflake_password,
        account=snowflake_account,
        warehouse="COMPUTE_WH",
        database="MACRO_PIPELINE",
        schema="PUBLIC",
    )
