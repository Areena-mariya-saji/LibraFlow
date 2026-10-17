# Module 5 — Serverless Architecture using AWS Lambda and API Gateway

This guide documents the serverless architecture implementation for **LibraFlow — Library Management System**. It covers Function-as-a-Service (FaaS), Amazon API Gateway endpoints, Amazon S3 event-driven triggers, local emulation, and AWS SAM deployment.

---

## 1. Serverless & Event-Driven Architecture Explained

### 1.1 What is Function-as-a-Service (FaaS)?
In traditional hosting (virtual machines or containers), a server process is always running, consuming CPU and memory even when idle. 
In **FaaS** (e.g. AWS Lambda):
* Code runs only in response to specific events (HTTP requests, file uploads, database changes).
* Infrastructure scales automatically from 0 to thousands of concurrent executions.
* Pricing is calculated strictly per millisecond of compute time consumed. When no requests arrive, cost is \$0.00.

### 1.2 Event-Driven Architecture
Rather than monolithic polling, components communicate by emitting and reacting to events:
```
[Client / Mobile App]
          │
          ▼ HTTP GET /books/availability
[Amazon API Gateway]
          │
          ▼ Invoke
[AWS Lambda: BookAvailabilityFunction]
          │
          ▼ Returns JSON
[JSON Response to Client]
```

```
[Librarian uploads catalog.csv]
          │
          ▼
[Amazon S3 Bucket]
          │
          ▼ Event: s3:ObjectCreated:Put
[AWS Lambda: S3EventProcessorFunction]
          │
          ▼ Logs sanitized metadata
[Amazon CloudWatch Logs]
```

---

## 2. Serverless Function Implementations

### Function A: Book Availability Public API (`book_availability_function.py`)
* **Trigger**: HTTP GET via API Gateway (`/books/availability`).
* **Purpose**: Returns real-time library inventory metrics (total titles, available copies, borrowed copies).
* **Sample Response**:
```json
{
  "library": "LibraFlow",
  "total_titles": 250,
  "available_copies": 180,
  "borrowed_copies": 70,
  "system_status": "operational",
  "timestamp": "2026-10-17T06:08:36.270868+00:00"
}
```

### Function B: Book Reservation API (`lambda_function.py`)
* **Trigger**: HTTP POST via API Gateway (`/books/reserve`).
* **Input Payload**: `{"book_id": 101, "member_id": 45}`.
* **Validation**: Checks that both `book_id` and `member_id` are provided. Returns HTTP 400 if validation fails, or HTTP 200 with an issued reservation token.
* **State Notice**: This microservice demonstrates stateless validation and queuing. For persistent cloud storage, items are dispatched to Amazon DynamoDB.

### Function C: S3 Event Trigger Processor (`s3_event_function.py`)
* **Trigger**: Amazon S3 `ObjectCreated` notification.
* **Purpose**: Ingests uploaded catalog backups or bulk digital library resources.
* **Privacy Guard**: Logs only sanitized object metadata (bucket, key, size, timestamp). **Never** logs file contents or private student identifiers.

---

## 3. Local Verification (No AWS Account Required)

BCA students can verify and demonstrate the complete serverless workflow locally on Windows without cloud billing:

```powershell
python serverless/test_local.py
```

*Output:*
```
=============================================================
 LibraFlow AWS Serverless Local Test Suite
=============================================================
--- [1/3] Testing Function A: Book Availability API (GET) ---
Status Code: 200
[PASS] Function A executed successfully.

--- [2/3] Testing Function B: Book Reservation API (POST) ---
Valid Request Status: 200
Invalid Request Status: 400
[PASS] Function B executed successfully.

--- [3/3] Testing Function C: S3 Event Trigger Processor ---
[+] S3 Upload Detected: Bucket='libraflow-catalog-bucket', ObjectKey='exports/catalog_inventory_2026.csv', Size=40960 bytes
Event Status: 200
[PASS] Function C executed successfully.
=============================================================
 ALL 3 SERVERLESS FUNCTIONS PASSED LOCAL VERIFICATION
=============================================================
```

---

## 4. Optional Cloud Deployment via AWS SAM

> [!NOTE]
> Cloud deployment is completely optional for BCA practical evaluation. If you do not possess an AWS account, demonstrate the local test suite above.

### Step 4.1 Configure AWS CLI Profile
Install the AWS CLI on Windows and configure a development profile:
```powershell
aws configure --profile libraflow-dev
```
Enter your AWS Access Key ID, Secret Access Key, and default region (`us-east-1`).
*Never commit credentials or `.aws/credentials` to Git.*

### Step 4.2 Build and Validate SAM Template
In the project root:
```powershell
cd serverless
sam validate
sam build
```

### Step 4.3 Deploy with AWS SAM
```powershell
sam deploy --guided --profile libraflow-dev
```
Prompts:
* Stack Name: `libraflow-serverless`
* AWS Region: `us-east-1`
* Parameter LibraryName: `LibraFlow`
* Allow SAM CLI to create IAM roles: `Y`
* Confirm changes before deploy: `Y`

### Step 4.4 Test Live Endpoints
Once deployment finishes, SAM outputs your live API Gateway URLs:

```powershell
# Test GET Availability
Invoke-RestMethod -Uri "https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/books/availability"

# Test POST Reservation
$headers = @{"Content-Type" = "application/json"}
$body = '{"book_id": 101, "member_id": 45}'
Invoke-RestMethod -Uri "https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/books/reserve" -Method Post -Headers $headers -Body $body
```

---

## 5. Security & Minimum Required IAM Permissions

Under the **Principle of Least Privilege**, Lambda execution roles are granted only the necessary IAM policies:

1. **`AWSLambdaBasicExecutionRole`**: Allows writing logs to Amazon CloudWatch (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`).
2. **S3 Read Access** (Function C only): `s3:GetObject` on the designated ingestion bucket only.

---

## 6. AWS Cost Considerations & Free-Tier Limitations

| Service | AWS Free-Tier Allowance | Cost Beyond Free Tier |
| :--- | :--- | :--- |
| **AWS Lambda** | 1,000,000 free requests per month + 3.2M seconds compute time. | \$0.20 per 1M requests. |
| **Amazon API Gateway** | 1,000,000 free API calls per month for 12 months. | \$1.00 per 1M calls. |
| **Amazon S3** | 5 GB standard storage + 20,000 GET / 2,000 PUT requests. | ~\$0.023 per GB-month. |

### Resource Cleanup
To prevent any unexpected charges after testing:
```powershell
sam delete --stack-name libraflow-serverless --profile libraflow-dev
```
Confirm stack deletion when prompted.
