import logging
from decimal import Decimal
from repository import IndividualReportRepository, TestReportRepository
from mock_data import get_grading_service_data, get_candidate_service_data, get_test_service_data, get_proctoring_service_data
from utils import get_current_time
import sns

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ReportingService:
    def __init__(self):
        self.individual_repo = IndividualReportRepository()
        self.test_repo = TestReportRepository()

    def generate_candidate_report(self, test_id, user_id):
        logger.info(f"Generating candidate report for testId: {test_id}, userId: {user_id}")
        
        grading_data = get_grading_service_data(test_id, user_id)
        candidate_data = get_candidate_service_data(user_id)
        proctoring_data = get_proctoring_service_data(test_id, user_id)
        
        report = {
            "testId": test_id,
            "userId": user_id,
            "candidateName": candidate_data.get("candidateName"),
            "score": Decimal(str(grading_data.get("score", 0))),
            "totalMarks": Decimal(str(grading_data.get("totalMarks", 0))),
            "percentage": Decimal(str(grading_data.get("percentage", 0))),
            "correctAnswers": grading_data.get("correctAnswers", 0),
            "wrongAnswers": grading_data.get("wrongAnswers", 0),
            "unanswered": grading_data.get("unanswered", 0),
            "timeTaken": Decimal(str(grading_data.get("timeTaken", 0))),
            "status": grading_data.get("status"),
            "submittedAt": grading_data.get("submittedAt"),
            "proctoringDetails": proctoring_data,
            "generatedAt": get_current_time()
        }
        
        self.individual_repo.create(report)
        return report

    def update_test_report(self, test_id):
        logger.info(f"Updating test report for testId: {test_id}")
        
        test_data = get_test_service_data(test_id)
        candidates = self.individual_repo.list_by_test(test_id)
        
        completed_candidates = len(candidates)
        passed_candidates = sum(1 for c in candidates if c.get("status") == "PASSED")
        failed_candidates = completed_candidates - passed_candidates
        
        total_score = sum(float(c.get("score", 0)) for c in candidates)
        average_score = total_score / completed_candidates if completed_candidates > 0 else 0
        
        scores = [float(c.get("score", 0)) for c in candidates]
        highest_score = max(scores) if scores else 0
        lowest_score = min(scores) if scores else 0
        
        pass_percentage = (passed_candidates / completed_candidates * 100) if completed_candidates > 0 else 0
        
        total_time = sum(float(c.get("timeTaken", 0)) for c in candidates)
        average_time_taken = total_time / completed_candidates if completed_candidates > 0 else 0
        
        total_warnings = sum(int(c.get("proctoringDetails", {}).get("warningCount", 0)) for c in candidates)
        average_warnings = total_warnings / completed_candidates if completed_candidates > 0 else 0
        
        existing_report = self.test_repo.get(test_id)
        generated_at = existing_report.get("generatedAt") if existing_report else get_current_time()
        
        report = {
            "testId": test_id,
            "testName": test_data.get("testName"),
            "totalCandidates": test_data.get("totalCandidates"),
            "completedCandidates": completed_candidates,
            "averageScore": Decimal(str(round(average_score, 2))),
            "highestScore": Decimal(str(round(highest_score, 2))),
            "lowestScore": Decimal(str(round(lowest_score, 2))),
            "passedCandidates": passed_candidates,
            "failedCandidates": failed_candidates,
            "passPercentage": Decimal(str(round(pass_percentage, 2))),
            "averageTimeTaken": Decimal(str(round(average_time_taken, 2))),
            "totalWarnings": Decimal(str(total_warnings)),
            "averageWarnings": Decimal(str(round(average_warnings, 2))),
            "generatedAt": generated_at,
            "lastUpdated": get_current_time()
        }
        
        self.test_repo.upsert(report)
        return report

    def generate_reports(self, test_id, user_id):
        logger.info(f"Starting report generation process for testId: {test_id}, userId: {user_id}")
        
        try:
            # Generate Individual Report
            self.generate_candidate_report(test_id, user_id)
            sns.publish_candidate_report_generated(test_id, user_id)
            
            # Update Test Report
            self.update_test_report(test_id)
            sns.publish_test_report_generated(test_id)
            
            logger.info(f"Report generation process completed for testId: {test_id}, userId: {user_id}")
        except Exception as e:
            logger.error(f"Failed to generate reports: {str(e)}")
