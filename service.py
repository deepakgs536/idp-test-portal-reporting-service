import logging
from decimal import Decimal
from repository import IndividualReportRepository, TestReportRepository
import base64
from mock_data import get_grading_service_data, get_candidate_service_data, get_test_service_data, get_proctoring_service_data
from utils import get_current_time
from datetime import datetime
import sns

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ReportingService:
    def __init__(self):
        self.individual_repo = IndividualReportRepository()
        self.test_repo = TestReportRepository()

    def generate_candidate_report(self, detail):
        test_id = detail.get("testId")
        mail_id = detail.get("mailId")
        logger.info(f"Generating candidate report for testId: {test_id}, mailId: {mail_id}")
        
        grading_data = get_grading_service_data(detail)
        candidate_data = get_candidate_service_data(mail_id)
        proctoring_data = get_proctoring_service_data(test_id, mail_id)
        
        time_taken = 0
        if proctoring_data and proctoring_data.get("startedAt") and proctoring_data.get("endedAt"):
            try:
                start_time = datetime.fromisoformat(proctoring_data["startedAt"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(proctoring_data["endedAt"].replace("Z", "+00:00"))
                time_taken = (end_time - start_time).total_seconds()
            except Exception as e:
                logger.error(f"Error calculating timeTaken: {e}")
        
        report = {
            "testId": test_id,
            "testName": grading_data.get("testName"),
            "mailId": mail_id,
            "candidateName": candidate_data.get("candidateName"),
            "college": candidate_data.get("college"),
            "mobile": candidate_data.get("mobile"),
            "score": Decimal(str(grading_data.get("score", 0))),
            "totalMarks": Decimal(str(grading_data.get("totalMarks", 0))),
            "percentage": Decimal(str(grading_data.get("percentage", 0))),
            "correctAnswers": grading_data.get("correctAnswers", 0),
            "wrongAnswers": grading_data.get("wrongAnswers", 0),
            "unanswered": grading_data.get("unanswered", 0),
            "timeTaken": Decimal(str(time_taken)),
            "status": grading_data.get("status"),
            "submittedAt": grading_data.get("submittedAt"),
            "sectionWisePerformance": grading_data.get("sections", []),
            "proctoringDetails": proctoring_data,
            "generatedAt": get_current_time()
        }
        
        self.individual_repo.create(report)
        sns.publish_candidate_report_generated(report)
        return report

    def update_candidate_coding_score(self, test_id, mail_id, new_score):
        logger.info(f"Updating CODING score for testId: {test_id}, mailId: {mail_id} to {new_score}")
        
        report = self.individual_repo.get(test_id, mail_id)
        if not report:
            return None
            
        sections = report.get("sectionWisePerformance", [])
        coding_section_found = False
        old_score = 0
        
        for sec in sections:
            if sec.get("sectionName") == "CODING":
                old_score = float(sec.get("score", 0))
                sec["score"] = Decimal(str(new_score))
                coding_section_found = True
                break
                
        if not coding_section_found:
            return None
            
        # Update overall score to reflect the change in the coding section
        score_diff = float(new_score) - old_score
        current_overall = float(report.get("score", 0))
        report["score"] = Decimal(str(current_overall + score_diff))
        
        # Recalculate percentage if totalMarks > 0
        total_marks = float(report.get("totalMarks", 0))
        if total_marks > 0:
            new_percentage = (float(report["score"]) / total_marks) * 100
            report["percentage"] = Decimal(str(round(new_percentage, 2)))
            
        self.individual_repo.create(report)
        
        # After updating the individual report, we should update the test report to reflect new averages
        self.update_test_report(test_id)
        
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
        
        section_wise_totals = {}
        for c in candidates:
            for sec in c.get("sectionWisePerformance", []):
                sec_id = sec.get("sectionId")
                if sec_id not in section_wise_totals:
                    section_wise_totals[sec_id] = {
                        "sectionName": sec.get("sectionName"),
                        "totalScore": 0,
                        "highestScore": 0,
                        "count": 0
                    }
                
                score = float(sec.get("score", 0))
                section_wise_totals[sec_id]["totalScore"] += score
                section_wise_totals[sec_id]["count"] += 1
                if score > section_wise_totals[sec_id]["highestScore"]:
                    section_wise_totals[sec_id]["highestScore"] = score
                    
        section_wise_averages = []
        for sec_id, data in section_wise_totals.items():
            avg = data["totalScore"] / data["count"] if data["count"] > 0 else 0
            section_wise_averages.append({
                "sectionId": sec_id,
                "sectionName": data["sectionName"],
                "averageScore": Decimal(str(round(avg, 2))),
                "highestScore": Decimal(str(round(data["highestScore"], 2)))
            })
        
        existing_report = self.test_repo.get(test_id)
        generated_at = existing_report.get("generatedAt") if existing_report else get_current_time()
        
        report = {
            "testId": test_id,
            "testName": test_data.get("testName"),
            "totalCandidates": test_data.get("totalCandidates"),
            "durationMinutes": test_data.get("durationMinutes"),
            "totalMarks": test_data.get("totalMarks"),
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
            "sectionWiseAverages": section_wise_averages,
            "generatedAt": generated_at,
            "lastUpdated": get_current_time()
        }
        
        self.test_repo.upsert(report)
        return report

    def generate_reports(self, detail):
        test_id = detail.get("testId")
        mail_id = detail.get("mailId")
        logger.info(f"Starting report generation process for testId: {test_id}, mailId: {mail_id}")
        
        try:
            # Generate Individual Report
            self.generate_candidate_report(detail)
            
            # Update Test Report
            self.update_test_report(test_id)
            sns.publish_test_report_generated(test_id)
            
            logger.info(f"Report generation process completed for testId: {test_id}, mailId: {mail_id}")
        except Exception as e:
            logger.error(f"Failed to generate reports: {str(e)}")

    def export_test_report(self, test_id):
        try:
            candidates = self.individual_repo.list_by_test(test_id)

            from report.excel_export import export_candidates_to_excel
            excel_file = export_candidates_to_excel(candidates)

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "Content-Disposition": f'attachment; filename="{test_id}_report.xlsx"'
                },
                "isBase64Encoded": True,
                "body": base64.b64encode(excel_file).decode("utf-8")
            }
        except Exception as e:
            logger.error(f"Error exporting test report: {str(e)}")
            return {
                "statusCode": 500,
                "body": "Error exporting test report"
            }
