import logging
from router import route_request
from sqs import process_sqs_event

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Received event")
    
    if 'Records' in event:
        # Check if it's an SQS event
        first_record = event['Records'][0]
        if first_record.get('eventSource') == 'aws:sqs':
            process_sqs_event(event)
            return {"statusCode": 200, "body": "SQS event processed successfully"}
            
    if 'httpMethod' in event or ('requestContext' in event and 'http' in event['requestContext']):
        # It's an API Gateway event (REST API v1.0 or HTTP API v2.0)
        return route_request(event)
        
    logger.warning("Unsupported event format. Please ensure Lambda Proxy Integration is enabled (for REST APIs) or you are using HTTP APIs.")
    return {"statusCode": 400, "body": "Unsupported event format. Ensure Lambda Proxy Integration is enabled."}
