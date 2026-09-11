# Reporting Service v2

This repository contains the completely refactored DK Test Platform Reporting Service. It is designed with a strict microservice architecture, separating asynchronous event processing (writes) from synchronous REST APIs (reads) to ensure scalability, maintainability, and safety against infinite recursive loops.

## Architecture & Code Structure

The service is split into two completely isolated packages. There is **no shared code** between these packages to ensure zero coupling between the API layer and the Event Worker layer. 

```
reporting-service-v2/
├── http_api/               # Handles API Gateway REST requests
│   ├── handler.py          # Lambda entry point
│   ├── router.py           # HTTP method and path routing
│   ├── controller.py       # Request validation & formatting
│   ├── service.py          # Business logic for updates & fetching
│   ├── repository.py       # DynamoDB access for reads/updates
│   ├── config.py           # Environment config
│   └── utils.py            # Shared utility functions
│
└── event_worker/           # Handles SQS asynchronous triggers
    ├── handler.py          # SQS Lambda entry point
    ├── processor.py        # Strict SQS payload validation (Loop Prevention)
    ├── service.py          # Core generation and aggregation logic
    ├── repository.py       # DynamoDB access for writes
    ├── external_clients.py # HTTP clients for Grading, Proctoring, etc.
    ├── sns_publisher.py    # Emits Candidate/Test Report Generated events
    ├── config.py           # Environment config
    └── utils.py            # Shared utility functions
```

## Infrastructure Constraints (As Requested)
- **No S3:** All data (including large candidate reports) is stored in Amazon DynamoDB.
- **No EventBridge:** All messaging relies on Amazon SQS and Amazon SNS.
- **Loop Prevention Built-In:** The `event_worker` strictly validates SQS payloads, refusing to process bounced Candidate Reports, securely preventing the catastrophic infinite loops experienced in v1.

## Environment Variables
Both Lambdas require the following environment variables:
- `AWS_REGION`: (default: `us-east-1`)
- `INDIVIDUAL_REPORTS_TABLE`: (default: `IndividualReports`)
- `TEST_REPORTS_TABLE`: (default: `TestReports`)
- `CANDIDATE_REPORT_TOPIC_ARN`: ARN for SNS topic
- `TEST_REPORT_TOPIC_ARN`: ARN for SNS topic
