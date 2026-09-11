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
            sqs_body = json.loads(record["body"])
            logger.info(f"SQS Body: {json.dumps(sqs_body)}")

            if "Message" in sqs_body:
                body = json.loads(sqs_body["Message"])
            else:
                body = sqs_body

            logger.info(f"Actual Event: {json.dumps(body)}")
            event_type = body.get("detailType") or body.get("eventType")
            
            # --- CRITICAL FIX: RECURSIVE LOOP PREVENTION ---
            # If the payload is actually a Candidate Report bounding back from SNS,
            # it will have candidateName and generatedAt. We MUST drop it instantly.
            if "generatedAt" in body and "candidateName" in body:
                logger.warning(f"Received a Candidate Report payload for testId: {body.get('testId')}. Ignoring to prevent recursive loop.")
                continue

            if event_type == 'GradeCompleted':
                detail = body.get("detail", {})
            else:
                # Fallback for new schema that lacks detailType wrapping
                detail = body

            test_id = detail.get("testId")
            mail_id = detail.get("mailId")

            if test_id and mail_id:
                logger.info(f"Processing GradeCompleted event for testId: {test_id}, mailId: {mail_id}")
                reporting_service.generate_reports(detail)
            else:
                logger.warning(f"Unhandled event type or missing testId/mailId. EventType: {event_type}")

        except Exception as e:
            logger.error(f"Error processing SQS record: {str(e)}")
            # Raise exception so the message fails and goes to DLQ (if configured)
            raise
