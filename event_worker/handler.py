import logging
from processor import process_sqs_event

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event Worker Lambda invoked")
    
    # Process SQS triggers
    if "Records" in event:
        process_sqs_event(event)
    else:
        logger.warning("No SQS Records found in event")
        
    return {
        "statusCode": 200,
        "body": "Processed successfully"
    }
