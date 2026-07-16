import json
import logging
from service import ReportingService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

reporting_service = ReportingService()

def process_sqs_event(event):
    logger.info("Processing SQS event")
    for record in event.get('Records', []):
        try:
            body = json.loads(record.get('body') or '{}')
            event_type = body.get('eventType')
            
            if event_type == 'GradeCompleted':
                test_id = body.get('testId')
                user_id = body.get('userId')
                if test_id and user_id:
                    logger.info(f"Processing GradeCompleted event for testId: {test_id}, userId: {user_id}")
                    reporting_service.generate_reports(test_id, user_id)
                else:
                    logger.warning("Missing testId or userId in GradeCompleted event")
            else:
                logger.info(f"Unhandled event type: {event_type}")
        except Exception as e:
            logger.error(f"Error processing SQS record: {str(e)}")
