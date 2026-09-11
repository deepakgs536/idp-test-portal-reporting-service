import os

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
INDIVIDUAL_REPORTS_TABLE = os.environ.get("INDIVIDUAL_REPORTS_TABLE", "IndividualReports")
TEST_REPORTS_TABLE = os.environ.get("TEST_REPORTS_TABLE", "TestReports")
CANDIDATE_REPORT_TOPIC_ARN = os.environ.get("CANDIDATE_REPORT_TOPIC_ARN", "")
TEST_REPORT_TOPIC_ARN = os.environ.get("TEST_REPORT_TOPIC_ARN", "")
