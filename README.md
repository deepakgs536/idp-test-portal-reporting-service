# Reporting Service

The Reporting Service is responsible for generating reports after the grading process is completed. It handles API Gateway requests and processes SQS events within a single AWS Lambda function. The service is written in Python 3.13, relies solely on standard libraries and `boto3`, and uses DynamoDB for storage and SNS for message publishing.

## Folder Structure

```
reporting-service/
├── handler.py       # Main Lambda entry point
├── router.py        # Routes API Gateway requests (supports HTTP API & REST API)
├── controller.py    # Request parsing and response formatting
├── service.py       # Business logic layer (ReportingService class)
├── repository.py    # DynamoDB data access layer
├── mock_data.py     # Mock responses for external services
├── sns.py           # SNS publishing utilities
├── sqs.py           # SQS event processing logic
├── dynamodb.py      # DynamoDB setup and table access
├── utils.py         # Shared utility functions (JSON Encoders, Time formatters)
├── config.py        # Environment variables configuration
├── requirements.txt # Python dependencies
└── README.md        # Project documentation
```

## Environment Variables

You must configure the following Environment Variables in your AWS Lambda function settings:

- `AWS_REGION`: AWS region (default: `us-east-1`)
- `INDIVIDUAL_REPORTS_TABLE`: DynamoDB table name for individual reports (default: `IndividualReports`)
- `TEST_REPORTS_TABLE`: DynamoDB table name for test reports (default: `TestReports`)
- `CANDIDATE_REPORT_TOPIC_ARN`: SNS topic ARN for CandidateReportGenerated event.
- `TEST_REPORT_TOPIC_ARN`: SNS topic ARN for TestReportGenerated event.

## Lambda Deployment Guide

### 1. Zipping the Project
You need to package the Python files into a ZIP archive.
Since the only dependency is `boto3` (which is pre-installed in the Lambda runtime), you don't need to install or package external virtual environments.

Run the following command inside the `reporting-service` directory:
- **Windows (PowerShell):** `Compress-Archive -Path * -DestinationPath function.zip`
- **Mac/Linux/Git Bash:** `zip -r function.zip . -x "*.git*"`

### 2. Creating the Lambda Function
1. Go to the AWS Management Console > **Lambda**.
2. Click **Create function** > **Author from scratch**.
3. **Name:** reporting-service
4. **Runtime:** Python 3.13
5. **Architecture:** x86_64 or arm64

### 3. Uploading Code & Configuring
1. Go to the **Code** tab.
2. Click **Upload from** > **.zip file** and select `function.zip`.
3. Go to **Runtime settings** > Edit.
4. Set **Handler** to: `handler.lambda_handler`

### 4. Permissions (IAM Role)
Go to **Configuration** > **Permissions** > Click the Execution Role name and attach:
- `AmazonDynamoDBFullAccess` (or scoped to specific tables)
- `AmazonSNSFullAccess` (or scoped to specific topics)
- `AmazonSQSFullAccess` (or scoped to specific queue)
- `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)

## Event Triggers Setup

### API Gateway Integration
1. Go to **Configuration** > **Triggers** > **Add trigger**.
2. Select **API Gateway**.
3. Create a new REST API or HTTP API. 
4. **IMPORTANT:** If you create a REST API, ensure **Lambda Proxy integration** is checked. The code supports both REST APIs and HTTP APIs seamlessly.

### SQS Integration
1. Go to **Configuration** > **Triggers** > **Add trigger**.
2. Select **SQS**.
3. Choose your designated Queue (e.g., `ReportingServiceQueue`).

## API Endpoints

Once your API Gateway is deployed, you will have access to the following endpoints under your API base URL:

- `POST /reports/generate`
  - **Description:** Generates a report manually.
  - **Payload:** `{"testId": "...", "userId": "..."}`
- `GET /reports/tests`
  - **Description:** Returns all Test Reports.
- `GET /reports/tests/{testId}`
  - **Description:** Returns a specific Test Report.
- `GET /reports/tests/{testId}/candidates`
  - **Description:** Returns all Individual Reports for a specific test.
- `GET /reports/tests/{testId}/candidates/{userId}`
  - **Description:** Returns a specific Individual Report.
- `DELETE /reports/tests/{testId}/candidates/{userId}`
  - **Description:** Deletes a specific Individual Report.
- `GET /health`
  - **Description:** Health check endpoint.

## Example Requests & Responses

### POST /reports/generate
**Request:**
```json
{
    "testId": "TEST001",
    "userId": "USER001"
}
```
**Response:**
```json
{
    "success": true,
    "message": "Report generation triggered successfully"
}
```

### GET /reports/tests/{testId}
**Response:**
```json
{
    "success": true,
    "message": "Fetched test report",
    "data": {
        "testId": "TEST001",
        "testName": "Java Fundamentals",
        "totalCandidates": 120,
        "completedCandidates": 1,
        "averageScore": 42.0,
        "highestScore": 42,
        "lowestScore": 42,
        "passedCandidates": 1,
        "failedCandidates": 0,
        "passPercentage": 100.0,
        "averageTimeTaken": 3120.0,
        "generatedAt": "2026-07-16T10:25:00Z",
        "lastUpdated": "2026-07-16T10:26:00Z"
    }
}
```

## Testing Locally (Sanity Check)

To verify the handler locally without AWS, create a `test_local.py` file in the root folder:

```python
import handler
print(handler.lambda_handler({"httpMethod": "GET", "resource": "/health"}, None))
```

Run it via `python test_local.py`. Note: Actual business logic testing requires valid AWS credentials and mocked AWS resources.
