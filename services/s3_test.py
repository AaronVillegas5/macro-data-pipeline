from services.s3_client import s3
import json

s3.put_object(
    Bucket="macro-data-pipeline-raw",
    Key="test/hello.json",
    Body=json.dumps({"test": "success"})
)
print("S3 upload successful")