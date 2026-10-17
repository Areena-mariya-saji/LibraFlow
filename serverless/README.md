# LibraFlow — Serverless Microservices Architecture

This directory implements the serverless architecture demonstrations for the BCA microproject syllabus (Module 5), utilizing **AWS Lambda**, **Amazon API Gateway**, and **Amazon S3 Event Notifications**.

## Component Overview

| File | Serverless Role | Trigger Source | Primary Function |
| :--- | :--- | :--- | :--- |
| `book_availability_function.py` | Function A | API Gateway (`GET /books/availability`) | Returns real-time JSON catalog metrics. |
| `lambda_function.py` | Function B | API Gateway (`POST /books/reserve`) | Validates reservation requests and assigns tokens. |
| `s3_event_function.py` | Function C | S3 Event (`s3:ObjectCreated:*`) | Ingests uploaded catalog backups and logs safe metadata. |
| `template.yaml` | AWS SAM Model | CloudFormation | Infrastructure as Code (IaC) deployment template. |
| `test_local.py` | Local Test Harness | Direct Python Invocation | Tests all 3 functions locally without an AWS account. |

## Running Local Verification

You do not need an AWS account or cloud billing to test these functions. Run the local test runner:
```powershell
python serverless/test_local.py
```

For complete instructions covering AWS CLI profiles, SAM deployment, IAM least privilege permissions, and AWS free-tier cost considerations, refer to [docs/module5-serverless.md](../docs/module5-serverless.md).
