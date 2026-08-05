import logging
import json
from router import route_request
from sqs import process_sqs_event

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event) if isinstance(event, dict) else event}")
    
    if 'Records' in event:
        # Check if it's an SQS event
        try:
            first_record = event['Records'][0]
            if first_record.get('eventSource') == 'aws:sqs':
                process_sqs_event(event)
                return {"statusCode": 200, "body": "SQS event processed successfully"}
        except Exception as e:
            logger.error(f"Error processing SQS event: {str(e)}")
            return {"statusCode": 500, "body": "Error processing SQS event"}
            
    if 'httpMethod' in event or ('requestContext' in event and 'http' in event['requestContext']):
        # It's an API Gateway event (REST API v1.0 or HTTP API v2.0)
        try:
            return route_request(event)
        except Exception as e:
            logger.error(f"Error routing request: {str(e)}")
            return {"statusCode": 500, "body": "Internal server error"}
        
    logger.warning("Unsupported event format. Please ensure Lambda Proxy Integration is enabled (for REST APIs) or you are using HTTP APIs.")
    return {"statusCode": 400, "body": "Unsupported event format. Ensure Lambda Proxy Integration is enabled."}
