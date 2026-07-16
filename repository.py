import logging
from boto3.dynamodb.conditions import Key
import dynamodb

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class IndividualReportRepository:
    def __init__(self):
        self.table = dynamodb.get_individual_reports_table()

    def create(self, report):
        try:
            self.table.put_item(Item=report)
            logger.info(f"Created individual report for testId: {report['testId']}, userId: {report['userId']}")
        except Exception as e:
            logger.error(f"Error creating individual report: {str(e)}")
            raise

    def get(self, test_id, user_id):
        try:
            response = self.table.get_item(Key={'testId': test_id, 'userId': user_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting individual report: {str(e)}")
            raise

    def list_by_test(self, test_id):
        try:
            response = self.table.query(
                KeyConditionExpression=Key('testId').eq(test_id)
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error listing individual reports by testId: {str(e)}")
            raise

    def delete(self, test_id, user_id):
        try:
            self.table.delete_item(Key={'testId': test_id, 'userId': user_id})
            logger.info(f"Deleted individual report for testId: {test_id}, userId: {user_id}")
        except Exception as e:
            logger.error(f"Error deleting individual report: {str(e)}")
            raise

class TestReportRepository:
    def __init__(self):
        self.table = dynamodb.get_test_reports_table()

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

    def list_all(self):
        try:
            response = self.table.scan()
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error listing all test reports: {str(e)}")
            raise
