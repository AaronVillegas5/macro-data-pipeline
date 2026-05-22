import boto3, json, os
from datetime import date, datetime
from utilities.logger import logger
from db.models import RawApiResponse
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def save_raw_to_s3(source, series_id, raw_response, start=None, end=None):
    bucket = os.getenv("S3_BUCKET_NAME")
    
    start = start or "unknown"
    end = end or "unknown"

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    key = (
        f"raw/{source}/{series_id}/"
        f"start={start}_end={end}/"
        f"{timestamp}.json"
    )

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(raw_response)
    )

    logger.info(f"Saved raw {source}/{series_id} to S3 at {key}")
def save_raw_response(source, identifier, raw_response, db_session, start=None, end=None):
    # Save to S3 (no db dependency)
    save_raw_to_s3(source, identifier, raw_response, start, end)

    # Save to Postgres
    record = RawApiResponse(
        source=source,
        identifier=identifier,
        raw_response=raw_response
    )

    db_session.add(record)
    db_session.commit()

    logger.info(f"Saved raw {source}/{identifier} to Postgres + S3")