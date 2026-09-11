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

    def get(self, test_id, mail_id):
        try:
            response = self.table.get_item(Key={'testId': test_id, 'mailId': mail_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting individual report: {str(e)}")
            raise

    def upsert(self, report: dict):
        try:
            self.table.put_item(Item=report)
        except Exception as e:
            logger.error(f"Error upserting individual report: {str(e)}")
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

    def delete(self, test_id, mail_id):
        try:
            self.table.delete_item(Key={'testId': test_id, 'mailId': mail_id})
            logger.info(f"Deleted individual report for testId: {test_id}, mailId: {mail_id}")
        except Exception as e:
            logger.error(f"Error deleting individual report: {str(e)}")
            raise

    def batch_delete(self, test_id, mail_ids):
        try:
            with self.table.batch_writer() as batch:
                for mail_id in mail_ids:
                    batch.delete_item(Key={'testId': test_id, 'mailId': mail_id})
            logger.info(f"Batch deleted {len(mail_ids)} reports for testId: {test_id}")
        except Exception as e:
            logger.error(f"Error batch deleting reports: {str(e)}")
            raise

class TestReportRepository:
    def __init__(self):
        self.table = dynamodb.Table(config.TEST_REPORTS_TABLE)

    def get(self, test_id):
        try:
            response = self.table.get_item(Key={'testId': test_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting test report: {str(e)}")
            raise

    def upsert(self, report: dict):
        try:
            self.table.put_item(Item=report)
        except Exception as e:
            logger.error(f"Error upserting test report: {str(e)}")
            raise

    def list_all(self):
        try:
            items = []
            response = self.table.scan()
            items.extend(response.get('Items', []))
            
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))
                
            return items
        except Exception as e:
            logger.error(f"Error listing all test reports: {str(e)}")
            raise

    def delete(self, test_id):
        try:
            self.table.delete_item(Key={'testId': test_id})
            logger.info(f"Deleted test report for testId: {test_id}")
        except Exception as e:
            logger.error(f"Error deleting test report: {str(e)}")
            raise
