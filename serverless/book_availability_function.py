import json
import os
from datetime import datetime, timezone


def lambda_handler(event, context):
    """
    AWS Lambda Handler: Book Availability API
    Triggered by: Amazon API Gateway (HTTP GET /books/availability)
    
    Returns high-level library catalog inventory metrics in JSON format.
    Uses configurable environment variables or realistic fallback demo data.
    """
    # Environment variables with fallback demo figures
    library_name = os.environ.get("LIBRARY_NAME", "LibraFlow")
    total_titles = int(os.environ.get("TOTAL_TITLES", "250"))
    available_copies = int(os.environ.get("AVAILABLE_COPIES", "180"))
    borrowed_copies = int(os.environ.get("BORROWED_COPIES", "70"))

    payload = {
        "library": library_name,
        "total_titles": total_titles,
        "available_copies": available_copies,
        "borrowed_copies": borrowed_copies,
        "system_status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS"
        },
        "body": json.dumps(payload)
    }
