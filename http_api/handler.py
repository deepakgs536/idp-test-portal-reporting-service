import logging
from router import route_request
from utils import build_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import json

def lambda_handler(event, context):
    logger.info(f"HTTP API Lambda invoked with event: {json.dumps(event)}")
    
    # Support both API Gateway V1 (REST API) and V2 (HTTP API) payloads
    is_v1 = "httpMethod" in event
    is_v2 = "requestContext" in event and "http" in event["requestContext"]
    
    if is_v1 or is_v2:
        return route_request(event)
    else:
        logger.warning("Event is not an API Gateway HTTP request")
        return build_response(400, False, "Invalid event format")
