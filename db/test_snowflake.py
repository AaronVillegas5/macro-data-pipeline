from db.snowflake_connection import get_snowflake_connection

def test_connection():
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()
        print(f"Connected successfully! Snowflake version: {version[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()