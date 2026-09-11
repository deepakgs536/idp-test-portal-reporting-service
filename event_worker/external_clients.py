import http.client
import json

def get_grading_service_data(detail):
    return {
        "testName": detail.get("testTitle") or "Unknown Test",
        "score": detail.get("score") or 0,
        "totalMarks": detail.get("totalMarks") or 0,
        "declaredTotalMarks": detail.get("declaredTotalMarks") or 0,
        "percentage": detail.get("percentage") or 0,
        "correctAnswers": detail.get("correctAnswers") or 0,
        "wrongAnswers": detail.get("wrongAnswers") or 0,
        "unanswered": detail.get("unanswered") or 0,
        "totalQuestions": detail.get("totalQuestions") or 0,
        "timeTaken": detail.get("timeTaken") or 0,
        "status": detail.get("status") or "FAILED",
        "submittedAt": detail.get("submittedAt"),
        "gradedAt": detail.get("gradedAt"),
        "sectionScores": detail.get("sectionScores", {}),
        "questionResults": detail.get("questionResults", []),
        "codingAnswers": detail.get("codingAnswers", []),
        "descriptiveAnswers": detail.get("descriptiveAnswers", [])
    }

def get_candidate_service_data(mail_id):
    conn = http.client.HTTPSConnection(
        "ylmuevgvjd.execute-api.ap-southeast-1.amazonaws.com",
        timeout=10
    )
    try:
        conn.request("GET", f"/user/{mail_id}")
        response = conn.getresponse()
        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.reason}")
        data = json.loads(response.read().decode("utf-8"))
        user = data.get("user", {})
        return {
            "candidateName": user.get("name", "Unknown User"),
            "college": user.get("college", "College not provided"),
            "mobile": user.get("mobile", "Mobile number not provided")
        }
    except Exception as e:
        print(f"Error calling Candidate Service: {e}")
        return {
            "candidateName": "DUMMY_USER_NAME",
            "college": "DUMMY_COLLEGE_NAME",
            "mobile": "DUMMY_MOBILE_NUMBER"
        }
    finally:
        conn.close()

def get_test_service_data(test_id):
    conn = http.client.HTTPSConnection(
        "utmtbogmaf.execute-api.ap-southeast-1.amazonaws.com",
        timeout=10
    )
    try:
        conn.request("GET", f"/tests/{test_id}")
        response = conn.getresponse()
        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.reason}")
        data = json.loads(response.read().decode("utf-8"))
        return {
            "testName": data.get("title", "Unknown Test"),
            "totalCandidates": data.get("totalCandidates", 0),
            "durationMinutes": data.get("durationMinutes", 0),
            "totalMarks": data.get("totalMarks", 100),
            "sections": data.get("sections", [])
        }
    except Exception as e:
        print(f"Error calling Test Service: {e}")
        return {
            "testName": "DUMMY_TEST_NAME",
            "totalCandidates": 0
        }
    finally:
        conn.close()

def get_proctoring_service_data(test_id, email):
    conn = http.client.HTTPSConnection(
        "dpm58qtugi.execute-api.ap-southeast-1.amazonaws.com",
        timeout=10
    )
    try:
        conn.request("GET", f"/proctoring/session/{email}")
        response = conn.getresponse()
        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.reason}")
        data = json.loads(response.read().decode("utf-8"))
        return {
            "sessionId": f"session_{email}",
            "examId": test_id,
            "email": email,
            "warningCount": data.get("warningCount", 0),
            "status": data.get("status"),
            "startedAt": data.get("startedTime"),
            "endedAt": data.get("endedTime"),
        }
    except Exception as e:
        print(f"Error calling Proctoring Service: {e}")
        return {
            "sessionId": f"session_{email}_dummy",
            "examId": test_id,
            "email": email,
            "warningCount": 0,
            "status": "DUMMY_DATA_FALLBACK",
            "startedAt": "2026-07-20T00:00:00Z",
            "endedAt": "2026-07-20T01:30:00Z",
        }
    finally:
        conn.close()
