import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda Handler: S3 Event Notification Processor
    Triggered by: Amazon S3 (s3:ObjectCreated:* events on catalog/document uploads)
    
    Security & Privacy Requirement:
    Logs a safe, anonymized summary of object metadata (bucket name, key, size).
    Strictly NEVER logs raw file contents or sensitive member information.
    """
    records = event.get("Records", [])
    processed_items = []

    print(f"[*] Received S3 event containing {len(records)} record(s).")

    for record in records:
        event_name = record.get("eventName", "unknown:event")
        event_time = record.get("eventTime", datetime.now(timezone.utc).isoformat())

        s3_data = record.get("s3", {})
        bucket_info = s3_data.get("bucket", {})
        bucket_name = bucket_info.get("name", "unknown-bucket")

        object_info = s3_data.get("object", {})
        object_key = object_info.get("key", "unknown-key")
        object_size = object_info.get("size", 0)

        # Sanitized safe summary
        safe_summary = {
            "bucket": bucket_name,
            "object_key": object_key,
            "size_bytes": object_size,
            "event_type": event_name,
            "event_time": event_time,
            "processing_status": "metadata_verified"
        }

        print(f"[+] S3 Upload Detected: Bucket='{bucket_name}', ObjectKey='{object_key}', Size={object_size} bytes")
        processed_items.append(safe_summary)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "service": "LibraFlow S3 Event Ingestion Service",
            "processed_records_count": len(processed_items),
            "records": processed_items
        })
    }
