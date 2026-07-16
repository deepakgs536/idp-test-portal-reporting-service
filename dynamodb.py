import boto3
import config

dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)

def get_individual_reports_table():
    return dynamodb.Table(config.INDIVIDUAL_REPORTS_TABLE)

def get_test_reports_table():
    return dynamodb.Table(config.TEST_REPORTS_TABLE)
