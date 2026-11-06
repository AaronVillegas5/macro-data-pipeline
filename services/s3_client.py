import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

from db.models import RawApiResponse
from utilities.logger import logger

load_dotenv()

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        try:
            import boto3

            _s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION"),
            )
        except Exception as exc:
            logger.warning(f"Failed to initialize S3 client: {exc}")
            return None
    return _s3_client


def save_raw_to_s3(source, series_id, raw_response, start=None, end=None):
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        return

    s3 = get_s3_client()
    if not s3:
        return

    start = start or "unknown"
    end = end or "unknown"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    key = f"raw/{source}/{series_id}/start={start}_end={end}/{timestamp}.json"

    try:
        s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(raw_response))
        logger.info(f"Saved raw {source}/{series_id} to S3 at {key}")
    except Exception as exc:
        logger.warning(f"S3 upload failed for {key}: {exc}")


def save_raw_response(source, identifier, raw_response, db_session, start=None, end=None):
    # Save to S3 (no db dependency)
    save_raw_to_s3(source, identifier, raw_response, start, end)

    # Save to Postgres
    if db_session:
        try:
            record = RawApiResponse(source=source, identifier=identifier, raw_response=raw_response)
            db_session.add(record)
            db_session.commit()
            logger.info(f"Saved raw {source}/{identifier} to Postgres + S3")
        except Exception as exc:
            db_session.rollback()
            logger.warning(f"Failed to save raw response to Postgres: {exc}")
