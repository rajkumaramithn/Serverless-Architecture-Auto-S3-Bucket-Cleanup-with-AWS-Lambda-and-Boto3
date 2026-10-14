import os
from datetime import datetime, timedelta, timezone

import boto3

# 1. Initialize the S3 client
s3 = boto3.client("s3")

BUCKET_NAME = os.environ.get("BUCKET_NAME", "your-bucket-name")
DEFAULT_RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))


def lambda_handler(event, context):
    event = event or {}

    # Retention can be overridden from the test event (useful for demos).
    if "retention_minutes" in event:
        age = timedelta(minutes=int(event["retention_minutes"]))
    else:
        age = timedelta(days=int(event.get("retention_days", DEFAULT_RETENTION_DAYS)))

    cutoff = datetime.now(timezone.utc) - age
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Deleting objects last modified before: {cutoff.isoformat()}")

    deleted = []
    kept = []

    # 2. List objects (paginator handles buckets with more than 1000 objects)
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # 3. Delete objects older than the cutoff
            if obj["LastModified"] < cutoff:
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                deleted.append(key)
                # 4. Log the deleted object's name
                print(f"Deleted: {key}")
            else:
                kept.append(key)

    print(f"Summary: {len(deleted)} deleted, {len(kept)} kept")
    return {"deleted": deleted, "kept": kept}
