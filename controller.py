import json
import logging
from utils import build_response
from service import ReportingService
from repository import IndividualReportRepository, TestReportRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

reporting_service = ReportingService()
individual_repo = IndividualReportRepository()
test_repo = TestReportRepository()

def generate_report(event):
    try:
        body = json.loads(event.get('body') or '{}')
        test_id = body.get('testId')
        mail_id = body.get('mailId')
        
        if not test_id or not mail_id:
            return build_response(400, False, "testId and mailId are required")
            
        reporting_service.generate_reports(test_id, mail_id)
        return build_response(200, True, "Report generation triggered successfully")
    except Exception as e:
        logger.error(f"Error in generate_report: {str(e)}")
        return build_response(500, False, "Internal server error")

def get_all_test_reports(event):
    try:
        reports = test_repo.list_all()
        return build_response(200, True, "Fetched test reports", reports)
    except Exception as e:
        logger.error(f"Error in get_all_test_reports: {str(e)}")
        return build_response(500, False, "Internal server error")

def get_test_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        report = test_repo.get(test_id)
        
        if not report:
            return build_response(404, False, "Test report not found")
            
        return build_response(200, True, "Fetched test report", report)
    except Exception as e:
        logger.error(f"Error in get_test_report: {str(e)}")
        return build_response(500, False, "Internal server error")

def get_test_candidates(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        reports = individual_repo.list_by_test(test_id)
        return build_response(200, True, "Fetched candidate reports", reports)
    except Exception as e:
        logger.error(f"Error in get_test_candidates: {str(e)}")
        return build_response(500, False, "Internal server error")

def get_candidate_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        mail_id = path_parameters.get('mailId')
        report = individual_repo.get(test_id, mail_id)
        
        if not report:
            return build_response(404, False, "Candidate report not found")
            
        return build_response(200, True, "Fetched candidate report", report)
    except Exception as e:
        logger.error(f"Error in get_candidate_report: {str(e)}")
        return build_response(500, False, "Internal server error")

def update_coding_score(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        mail_id = path_parameters.get('mailId')
        
        body = json.loads(event.get('body') or '{}')
        new_score = body.get('score')
        
        if new_score is None:
            return build_response(400, False, "score is required in request body")
            
        report = reporting_service.update_candidate_coding_score(test_id, mail_id, new_score)
        if not report:
            return build_response(404, False, "Candidate report not found or CODING section missing")
            
        return build_response(200, True, "Updated coding score successfully", report)
    except Exception as e:
        logger.error(f"Error in update_coding_score: {str(e)}")
        return build_response(500, False, "Internal server error")

def delete_candidate_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        mail_id = path_parameters.get('mailId')
        
        # Check if exists
        report = individual_repo.get(test_id, mail_id)
        if not report:
            return build_response(404, False, "Candidate report not found")
            
        individual_repo.delete(test_id, mail_id)
        return build_response(200, True, "Deleted candidate report")
    except Exception as e:
        logger.error(f"Error in delete_candidate_report: {str(e)}")
        return build_response(500, False, "Internal server error")

def health_check(event):
    return build_response(200, True, "Service is healthy")

def export_test_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        return reporting_service.export_test_report(test_id)
    except Exception as e:
        logger.error(f"Error in export_test_report: {str(e)}")
        return build_response(500, False, "Internal server error")
