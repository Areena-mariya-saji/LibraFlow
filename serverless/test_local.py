"""
LibraFlow Serverless Local Test Runner
Executes all 3 AWS Lambda functions locally with simulated API Gateway and S3 events.
Allows college lab evaluation without requiring an active AWS account or cloud expenditure.
"""

import sys
import json
from pathlib import Path

# Add serverless folder to sys.path
SERVERLESS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SERVERLESS_DIR))

import book_availability_function
import lambda_function as reservation_function
import s3_event_function


def test_availability_api():
    print("--- [1/3] Testing Function A: Book Availability API (GET) ---")
    event = {
        "httpMethod": "GET",
        "path": "/books/availability"
    }
    response = book_availability_function.lambda_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response["body"])
    print("Response Body:", json.dumps(body, indent=2))
    assert response["statusCode"] == 200
    assert body["library"] == "LibraFlow"
    assert body["total_titles"] > 0
    print("[PASS] Function A executed successfully.\n")


def test_reservation_api():
    print("--- [2/3] Testing Function B: Book Reservation API (POST) ---")
    
    # 1. Valid Request
    valid_event = {
        "httpMethod": "POST",
        "path": "/books/reserve",
        "body": json.dumps({"book_id": 101, "member_id": 45})
    }
    res_valid = reservation_function.lambda_handler(valid_event, None)
    print(f"Valid Request Status: {res_valid['statusCode']}")
    body_valid = json.loads(res_valid["body"])
    print("Valid Response:", json.dumps(body_valid, indent=2))
    assert res_valid["statusCode"] == 200
    assert body_valid["status"] == "success"
    assert "reservation_reference" in body_valid

    # 2. Invalid Request (Missing member_id)
    invalid_event = {
        "httpMethod": "POST",
        "path": "/books/reserve",
        "body": json.dumps({"book_id": 101})
    }
    res_invalid = reservation_function.lambda_handler(invalid_event, None)
    print(f"Invalid Request Status: {res_invalid['statusCode']}")
    assert res_invalid["statusCode"] == 400
    print("[PASS] Function B executed successfully.\n")


def test_s3_event_trigger():
    print("--- [3/3] Testing Function C: S3 Event Trigger Processor ---")
    synthetic_s3_event = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2026-10-17T06:30:00.000Z",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {
                        "name": "libraflow-catalog-bucket",
                        "arn": "arn:aws:s3:::libraflow-catalog-bucket"
                    },
                    "object": {
                        "key": "exports/catalog_inventory_2026.csv",
                        "size": 40960
                    }
                }
            }
        ]
    }
    response = s3_event_function.lambda_handler(synthetic_s3_event, None)
    print(f"Event Status: {response['statusCode']}")
    body = json.loads(response["body"])
    print("Processed Output:", json.dumps(body, indent=2))
    assert response["statusCode"] == 200
    assert body["processed_records_count"] == 1
    print("[PASS] Function C executed successfully.\n")


if __name__ == "__main__":
    print("=============================================================")
    print(" LibraFlow AWS Serverless Local Test Suite")
    print("=============================================================\n")
    test_availability_api()
    test_reservation_api()
    test_s3_event_trigger()
    print("=============================================================")
    print(" ALL 3 SERVERLESS FUNCTIONS PASSED LOCAL VERIFICATION")
    print("=============================================================")
