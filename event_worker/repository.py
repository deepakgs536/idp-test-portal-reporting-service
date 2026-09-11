import logging
import boto3
from boto3.dynamodb.conditions import Key
import config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)

class IndividualReportRepository:
    def __init__(self):
        self.table = dynamodb.Table(config.INDIVIDUAL_REPORTS_TABLE)

    def create(self, report):
        try:
            self.table.put_item(Item=report)
            logger.info(f"Created individual report for testId: {report['testId']}, mailId: {report['mailId']}")
        except Exception as e:
            logger.error(f"Error creating individual report: {str(e)}")
            raise

    def get(self, test_id, mail_id):
        try:
            response = self.table.get_item(Key={'testId': test_id, 'mailId': mail_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting individual report: {str(e)}")
            raise

    def list_by_test(self, test_id):
        try:
            items = []
            response = self.table.query(
                KeyConditionExpression=Key('testId').eq(test_id),
                ConsistentRead=True
            )
            items.extend(response.get('Items', []))
            
            while 'LastEvaluatedKey' in response:
                response = self.table.query(
                    KeyConditionExpression=Key('testId').eq(test_id),
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    ConsistentRead=True
                )
                items.extend(response.get('Items', []))
                
            return items
        except Exception as e:
            logger.error(f"Error listing individual reports by testId: {str(e)}")
            raise

class TestReportRepository:
    def __init__(self):
        self.table = dynamodb.Table(config.TEST_REPORTS_TABLE)

    def upsert(self, report):
        try:
            self.table.put_item(Item=report)
            logger.info(f"Upserted test report for testId: {report['testId']}")
        except Exception as e:
            logger.error(f"Error upserting test report: {str(e)}")
            raise

    def get(self, test_id):
        try:
            response = self.table.get_item(Key={'testId': test_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting test report: {str(e)}")
            raise
