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
            # Parse SQS body
            sqs_body = json.loads(record["body"])
            logger.info(f"SQS Body: {json.dumps(sqs_body)}")

            # SNS -> SQS wrapper
            if "Message" in sqs_body:
                body = json.loads(sqs_body["Message"])
            else:
                body = sqs_body

            logger.info(f"Actual Event: {json.dumps(body)}")
            event_type = body.get("detailType")
            
            if event_type == 'GradeCompleted':
                detail = body.get("detail", {})
                logger.info(f"Event Graded Details: {detail}")
                test_id = detail.get("testId")
                mail_id = detail.get("mailId")

                if test_id and mail_id:
                    logger.info(f"Processing GradeCompleted event for testId: {test_id}, mailId: {mail_id}")
                    reporting_service.generate_reports(detail)
                else:
                    logger.warning("Missing testId or mailId in GradeCompleted event")
            else:
                logger.info(f"Unhandled event type: {event_type}")
        except Exception as e:
            logger.error(f"Error processing SQS record: {str(e)}")
