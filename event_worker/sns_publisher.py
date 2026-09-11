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
    import decimal
    
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            return super(DecimalEncoder, self).default(obj)

    try:
        publish_message(
            config.CANDIDATE_REPORT_TOPIC_ARN,
            json.loads(json.dumps(report, cls=DecimalEncoder))
        )
    except Exception as e:
        logger.error(f"Error publishing message to SNS: {str(e)}")
    
def publish_test_report_generated(test_id):
    message = {
        "eventType": "TestReportGenerated",
        "testId": test_id
    }
    publish_message(config.TEST_REPORT_TOPIC_ARN, message)
