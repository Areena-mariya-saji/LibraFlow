import json
import uuid
from datetime import datetime, timezone


def lambda_handler(event, context):
    """
    AWS Lambda Handler: Book Reservation API
    Triggered by: Amazon API Gateway (HTTP POST /books/reserve)
    
    Accepts JSON body: {"book_id": 101, "member_id": 45}
    Validates input parameters and issues a reservation reference token.
    
    Architecture Note:
    This serverless microservice performs stateless schema validation and queue assignment.
    In cloud deployments, persistent ledger state is saved to Amazon DynamoDB or RDS.
    """
    http_method = event.get("httpMethod", "POST")
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": ""
        }

    # Extract request payload
    body_raw = event.get("body", "{}")
    if isinstance(body_raw, str):
        try:
            body = json.loads(body_raw) if body_raw else {}
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Bad Request",
                    "message": "Invalid JSON payload."
                })
            }
    else:
        body = body_raw or {}

    book_id = body.get("book_id")
    member_id = body.get("member_id")

    # Validation
    if not book_id or not member_id:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Unprocessable Entity",
                "message": "Both 'book_id' and 'member_id' are mandatory fields for reservation."
            })
        }

    # Generate reservation reference
    reservation_id = f"RES-AWS-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    response_data = {
        "status": "success",
        "message": f"Reservation queued successfully for Book ID {book_id}",
        "reservation_reference": reservation_id,
        "book_id": book_id,
        "member_id": member_id,
        "reservation_status": "pending_allocation",
        "created_at": timestamp,
        "backend": "AWS Lambda Serverless Function"
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(response_data)
    }
