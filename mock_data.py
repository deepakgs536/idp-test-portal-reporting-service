def get_grading_service_data(test_id, user_id):
    return {
        "score": 42,
        "totalMarks": 50,
        "percentage": 84,
        "correctAnswers": 42,
        "wrongAnswers": 6,
        "unanswered": 2,
        "timeTaken": 3120,
        "status": "PASSED",
        "submittedAt": "2026-07-16T10:25:00Z"
    }

def get_candidate_service_data(user_id):
    return {
        "candidateName": "John Doe"
    }

def get_test_service_data(test_id):
    return {
        "testName": "Java Fundamentals",
        "totalCandidates": 120
    }

def get_proctoring_service_data(test_id, user_id):
    return {
        "sessionId": f"session_{user_id}",
        "examId": test_id,
        "studentId": user_id,
        "warningCount": 3,
        "status": "ACTIVE",
        "startedAt": "2026-07-16T10:00:00Z",
        "endedAt": "2026-07-16T11:00:00Z"
    }
