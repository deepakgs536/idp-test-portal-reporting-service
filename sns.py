import boto3
import json
import logging
import config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client('sns', region_name=config.AWS_REGION)

def publish_message(topic_arn, message):
    if not topic_arn:
        logger.warning(f"SNS Topic ARN is missing. Would have published: {json.dumps(message)}")
        return

    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=json.dumps(message)
        )
        logger.info(f"Published message to {topic_arn}. MessageId: {response.get('MessageId')}")
    except Exception as e:
        logger.error(f"Error publishing message to SNS: {str(e)}")

def publish_candidate_report_generated(report: dict):

    message = {
        "eventType": "CandidateReportGenerated",
        "data": {
            "testId": report["testId"],
            "mailId": report["mailId"],
            "candidateName": report["candidateName"],
            "college": report["college"],
            "score": float(report["score"]),
            "percentage": float(report["percentage"]),
            "timeTaken": float(report["timeTaken"]),
            "warningCount": report["proctoringDetails"].get("warningCount", 0)
                if report.get("proctoringDetails")
                else 0,
            "status": report["status"],
            "generatedAt": report["generatedAt"]
        }
    }
    try:
        publish_message(
            config.CANDIDATE_REPORT_TOPIC_ARN,
            message
        )
    except Exception as e:
        logger.error(f"Error publishing message to SNS: {str(e)}")
    

def publish_test_report_generated(test_id):
    message = {
        "eventType": "TestReportGenerated",
        "testId": test_id
    }
    publish_message(config.TEST_REPORT_TOPIC_ARN, message)
