import json
import logging
import urllib.parse
from utils import build_response
from service import ReportingService
from repository import IndividualReportRepository, TestReportRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

reporting_service = ReportingService()
individual_repo = IndividualReportRepository()
test_repo = TestReportRepository()

def parse_body(event):
    body_str = event.get('body') or '{}'
    if event.get('isBase64Encoded'):
        import base64
        body_str = base64.b64decode(body_str).decode('utf-8')
    return json.loads(body_str)

def generate_report(event):
    try:
        body = parse_body(event)
        test_id = body.get('testId')
        mail_id = body.get('mailId')
        
        if not test_id or not mail_id:
            return build_response(400, False, "testId and mailId are required")
            
        reporting_service.generate_reports({
            "testId": test_id,
            "mailId": mail_id
        })
        return build_response(200, True, "Report generation triggered successfully")
    except Exception as e:
        logger.error(f"Error in generate_report: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

def get_all_test_reports(event):
    try:
        reports = test_repo.list_all()
        # Removed N+1 query loops that fetched candidates for every test report.
        # This prevents massive DynamoDB throttling and latency spikes.
        return build_response(200, True, "Fetched test reports", reports)
    except Exception as e:
        logger.error(f"Error in get_all_test_reports: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

def get_test_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        report = test_repo.get(test_id)
        
        if not report:
            return build_response(404, False, "Test report not found")
            
        needs_patch = not report.get("totalCandidates") or "totalTerminated" not in report or "totalCompleted" not in report
        
        if needs_patch:
            candidates = individual_repo.list_by_test(test_id)
            if not report.get("totalCandidates"):
                report["totalCandidates"] = len(candidates)
            if "totalTerminated" not in report or "totalCompleted" not in report:
                report["totalTerminated"] = sum(1 for c in candidates if str((c.get("proctoringDetails") or {}).get("status") or "").lower() == "terminated")
                report["totalCompleted"] = sum(1 for c in candidates if str((c.get("proctoringDetails") or {}).get("status") or "").lower() == "success")
            
        return build_response(200, True, "Fetched test report", report)
    except Exception as e:
        logger.error(f"Error in get_test_report: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

def get_test_candidates(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        
        query_string_parameters = event.get('queryStringParameters') or {}
        limit = int(query_string_parameters.get('limit', 10))
        
        # Enforce maximum limit of 100 to prevent payload exhaustion
        if limit > 100:
            limit = 100
            
        page = int(query_string_parameters.get('page', 1))
        
        all_reports = individual_repo.list_by_test(test_id)
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_reports = all_reports[start_idx:end_idx]
        
        total_reports = len(all_reports)
        total_pages = (total_reports + limit - 1) // limit
        
        response_data = {
            'reports': paginated_reports,
            'page': page,
            'limit': limit,
            'totalPages': total_pages,
            'totalReports': total_reports
        }
        
        return build_response(200, True, "Fetched candidate reports", response_data)
    except Exception as e:
        logger.error(f"Error in get_test_candidates: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

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
        return build_response(500, False, f"Internal server error: {str(e)}")

def update_coding_score(event, path_parameters):
    try:
        test_id = urllib.parse.unquote(path_parameters.get('testId', ''))
        mail_id = urllib.parse.unquote(path_parameters.get('mailId', ''))
        
        body = parse_body(event)
        new_score = body.get('score')
        
        if new_score is None:
            return build_response(400, False, "score is required in request body")
            
        report = reporting_service.update_candidate_coding_score(test_id, mail_id, new_score)
        if not report:
            return build_response(404, False, "Candidate report not found or CODING section missing")
            
        return build_response(200, True, "Updated coding score successfully", report)
    except Exception as e:
        logger.error(f"Error in update_coding_score: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

def update_question_score(event, path_parameters):
    try:
        test_id = urllib.parse.unquote(path_parameters.get('testId', ''))
        mail_id = urllib.parse.unquote(path_parameters.get('mailId', ''))
        question_id = urllib.parse.unquote(path_parameters.get('questionId', ''))
        
        body = parse_body(event)
        new_score = body.get('score')
        
        if new_score is None:
            return build_response(400, False, "score is required in request body")
            
        report = reporting_service.update_candidate_question_score(test_id, mail_id, question_id, new_score)
        if not report:
            return build_response(404, False, "Candidate report or specific question not found")
            
        return build_response(200, True, "Updated question score successfully", report)
    except Exception as e:
        logger.error(f"Error in update_question_score: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

def delete_candidate_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        mail_id = path_parameters.get('mailId')
        
        report = individual_repo.get(test_id, mail_id)
        if not report:
            return build_response(404, False, "Candidate report not found")
            
        individual_repo.delete(test_id, mail_id)
        return build_response(200, True, "Deleted candidate report")
    except Exception as e:
        logger.error(f"Error in delete_candidate_report: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

def delete_test_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        
        report = test_repo.get(test_id)
        if not report:
            return build_response(404, False, "Test report not found")
        candidates = individual_repo.list_by_test(test_id)
        
        # Batch delete candidates to prevent API Gateway timeout on large tests
        mail_ids = [c.get('mailId') for c in candidates if c.get('mailId')]
        if mail_ids:
            individual_repo.batch_delete(test_id, mail_ids)
                
        test_repo.delete(test_id)
        
        return build_response(200, True, "Deleted test report and associated candidate reports")
    except Exception as e:
        logger.error(f"Error in delete_test_report: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")

def health_check(event):
    return build_response(200, True, "Service is healthy")

def export_test_report(event, path_parameters):
    try:
        test_id = path_parameters.get('testId')
        return reporting_service.export_test_report(test_id)
    except Exception as e:
        logger.error(f"Error in export_test_report: {str(e)}")
        return build_response(500, False, f"Internal server error: {str(e)}")
