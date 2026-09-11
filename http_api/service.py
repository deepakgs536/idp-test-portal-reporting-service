import logging
from decimal import Decimal
import base64
from repository import IndividualReportRepository, TestReportRepository
from external_clients import get_grading_service_data, get_candidate_service_data, get_test_service_data, get_proctoring_service_data
from utils import get_current_time
from datetime import datetime
import sns_publisher as sns

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
        
        score = float(grading_data.get("score", 0))
        declared_total_marks = float(grading_data.get("declaredTotalMarks", 0))
        
        percentage = (score / declared_total_marks * 100) if declared_total_marks > 0 else 0
        status = "PASSED" if percentage >= 50 else "FAILED"
        
        report = {
            "testId": test_id,
            "testName": grading_data.get("testName"),
            "mailId": mail_id,
            "candidateName": candidate_data.get("candidateName"),
            "college": candidate_data.get("college"),
            "mobile": candidate_data.get("mobile"),
            "score": Decimal(str(score)),
            "totalMarks": Decimal(str(grading_data.get("totalMarks", 0))),
            "declaredTotalMarks": Decimal(str(declared_total_marks)),
            "percentage": Decimal(str(round(percentage, 2))),
            "correctAnswers": grading_data.get("correctAnswers", 0),
            "wrongAnswers": grading_data.get("wrongAnswers", 0),
            "unanswered": grading_data.get("unanswered", 0),
            "totalQuestions": grading_data.get("totalQuestions", 0),
            "timeTaken": Decimal(str(time_taken)),
            "status": status,
            "submittedAt": grading_data.get("submittedAt"),
            "gradedAt": grading_data.get("gradedAt"),
            "sectionScores": grading_data.get("sectionScores", {}),
            "questionResults": grading_data.get("questionResults", []),
            "codingAnswers": grading_data.get("codingAnswers", []),
            "descriptiveAnswers": grading_data.get("descriptiveAnswers", []),
            "proctoringDetails": proctoring_data,
            "generatedAt": get_current_time()
        }
        
        self.individual_repo.upsert(report)
        sns.publish_candidate_report_generated(report)
        return report

    def update_candidate_coding_score(self, test_id, mail_id, new_score):
        logger.info(f"Updating CODING score for testId: {test_id}, mailId: {mail_id} to {new_score}")
        
        report = self.individual_repo.get(test_id, mail_id)
        if not report:
            return None
            
        if not report.get("sectionScores"):
            report["sectionScores"] = {}
            
        old_score = float(report["sectionScores"].get("CODING", 0))
        report["sectionScores"]["CODING"] = Decimal(str(new_score))
        
        score_diff = float(new_score) - old_score
        current_overall = float(report.get("score", 0))
        report["score"] = Decimal(str(current_overall + score_diff))
        
        declared_total_marks = float(report.get("declaredTotalMarks", 0))
        if declared_total_marks > 0:
            new_percentage = (float(report["score"]) / declared_total_marks) * 100
            report["percentage"] = Decimal(str(round(new_percentage, 2)))
            report["status"] = "PASSED" if new_percentage >= 50 else "FAILED"
            
        self.individual_repo.upsert(report)
        sns.publish_candidate_report_generated(report)
        self.update_test_report(test_id)
        return report

    def update_candidate_question_score(self, test_id, mail_id, question_id, new_score):
        logger.info(f"Updating score for questionId: {question_id}, testId: {test_id}, mailId: {mail_id} to {new_score}")
        
        report = self.individual_repo.get(test_id, mail_id)
        if not report:
            return None
            
        question_found = False
        score_diff = 0
        section_name = None
        
        arrays_to_check = [
            report.get("codingAnswers") or [],
            report.get("descriptiveAnswers") or []
        ]
        
        for q_array in arrays_to_check:
            for q in q_array:
                if q.get("questionId") == question_id:
                    old_score = float(q.get("score", 0)) if "score" in q else 0.0
                    q["score"] = Decimal(str(new_score))
                    score_diff = float(new_score) - old_score
                    section_name = q.get("sectionName")
                    question_found = True
                    break
            if question_found:
                break
                
        if not question_found:
            return None
            
        if section_name:
            if not report.get("sectionScores"):
                report["sectionScores"] = {}
            current_sec_score = float(report["sectionScores"].get(section_name, 0))
            report["sectionScores"][section_name] = Decimal(str(current_sec_score + score_diff))
            
        current_overall = float(report.get("score", 0))
        report["score"] = Decimal(str(current_overall + score_diff))
        
        declared_total_marks = float(report.get("declaredTotalMarks", 0))
        if declared_total_marks > 0:
            new_percentage = (float(report["score"]) / declared_total_marks) * 100
            report["percentage"] = Decimal(str(round(new_percentage, 2)))
            report["status"] = "PASSED" if new_percentage >= 50 else "FAILED"
            
        self.individual_repo.upsert(report)
        sns.publish_candidate_report_generated(report)
        self.update_test_report(test_id)
        return report

    def update_test_report(self, test_id):
        logger.info(f"Updating test report for testId: {test_id}")
        
        test_data = get_test_service_data(test_id)
        candidates = self.individual_repo.list_by_test(test_id)
        
        completed_candidates = len(candidates)
        passed_candidates = sum(1 for c in candidates if c.get("status") == "PASSED")
        failed_candidates = completed_candidates - passed_candidates
        
        total_score = sum(float(c.get("score") or 0) for c in candidates)
        average_score = total_score / completed_candidates if completed_candidates > 0 else 0
        
        scores = [float(c.get("score") or 0) for c in candidates]
        highest_score = max(scores) if scores else 0
        lowest_score = min(scores) if scores else 0
        
        pass_percentage = (passed_candidates / completed_candidates * 100) if completed_candidates > 0 else 0
        
        total_time = sum(float(c.get("timeTaken") or 0) for c in candidates)
        average_time_taken = total_time / completed_candidates if completed_candidates > 0 else 0
        
        total_warnings = sum(int((c.get("proctoringDetails") or {}).get("warningCount") or 0) for c in candidates)
        average_warnings = total_warnings / completed_candidates if completed_candidates > 0 else 0
        
        section_wise_totals = {}
        for c in candidates:
            sec_scores = c.get("sectionScores") or {}
            for sec_name, score in sec_scores.items():
                if sec_name not in section_wise_totals:
                    section_wise_totals[sec_name] = {
                        "sectionName": sec_name,
                        "sectionType": sec_name,
                        "totalScore": 0,
                        "highestScore": 0,
                        "count": 0
                    }
                
                score_val = float(score or 0)
                section_wise_totals[sec_name]["totalScore"] += score_val
                section_wise_totals[sec_name]["count"] += 1
                if score_val > section_wise_totals[sec_name]["highestScore"]:
                    section_wise_totals[sec_name]["highestScore"] = score_val
                    
        section_wise_averages = []
        for sec_name, data in section_wise_totals.items():
            avg = data["totalScore"] / data["count"] if data["count"] > 0 else 0
            section_wise_averages.append({
                "sectionId": sec_name,
                "sectionName": data["sectionName"],
                "averageScore": Decimal(str(round(avg, 2))),
                "highestScore": Decimal(str(round(data["highestScore"], 2)))
            })
        
        existing_report = self.test_repo.get(test_id)
        generated_at = existing_report.get("generatedAt") if existing_report else get_current_time()
        
        unique_section_types = list(set([data.get("sectionType") for data in section_wise_totals.values() if data.get("sectionType")]))
        top_level_section_type = unique_section_types[0] if len(unique_section_types) == 1 else unique_section_types
        
        total_terminated = sum(1 for c in candidates if str((c.get("proctoringDetails") or {}).get("status") or "").lower() == "terminated")
        total_completed = sum(1 for c in candidates if str((c.get("proctoringDetails") or {}).get("status") or "").lower() == "success")

        total_candidates = test_data.get("totalCandidates", 0)
        if not total_candidates:
            total_candidates = completed_candidates

        report = {
            "testId": test_id,
            "testName": test_data.get("testName"),
            "sectionType": top_level_section_type,
            "totalCandidates": total_candidates,
            "durationMinutes": Decimal(str(test_data.get("durationMinutes"))) if test_data.get("durationMinutes") is not None else None,
            "totalMarks": Decimal(str(test_data.get("totalMarks"))) if test_data.get("totalMarks") is not None else None,
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
            "totalTerminated": total_terminated,
            "totalCompleted": total_completed,
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
            self.generate_candidate_report(detail)
            self.update_test_report(test_id)
            sns.publish_test_report_generated(test_id)
            logger.info(f"Report generation process completed for testId: {test_id}, mailId: {mail_id}")
        except Exception as e:
            logger.error(f"Failed to generate reports: {str(e)}")
            raise

    def export_test_report(self, test_id):
        try:
            candidates = self.individual_repo.list_by_test(test_id)
            # Assuming excel_export is handled elsewhere or you have the module
            # For strict preservation, we keep the identical dynamic import:
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
