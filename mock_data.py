import http.client
import json

PROCTORING_SERVICE_URL = "https://dpm58qtugi.execute-api.ap-southeast-1.amazonaws.com"

def get_grading_service_data(detail):
    return {
        "testName": detail.get("testTitle"),
        "score": detail.get("score"),
        "totalMarks": detail.get("totalMarks"),
        "percentage": detail.get("percentage"),
        "correctAnswers": detail.get("correctAnswers"),
        "wrongAnswers": detail.get("wrongAnswers"),
        "unanswered": detail.get("unanswered"),
        "timeTaken": detail.get("timeTaken"),
        "status": detail.get("status"),
        "submittedAt": detail.get("submittedAt")
    }

def get_candidate_service_data(mail_id):
    conn = http.client.HTTPSConnection(
        "ylmuevgvjd.execute-api.ap-southeast-1.amazonaws.com",
        timeout=10
    )

    try:
        conn.request(
            "GET",
            f"/user/{mail_id}"
        )

        response = conn.getresponse()

        print(f"actual response: {response}...")

        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.reason}")

        data = json.loads(response.read().decode("utf-8"))

        print(f"actual data: {data}...")

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
        conn.request(
            "GET",
            f"/tests/{test_id}"
        )

        response = conn.getresponse()

        print(f"actual response: {response}...")

        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.reason}")

        data = json.loads(response.read().decode("utf-8"))

        print(f"actual data: {data}...")

        return {
            "testName": data.get("title", "Unknown Test"),
            "totalCandidates": data.get("totalCandidates", 0),
            "durationMinutes": data.get("durationMinutes", 0),
            "totalMarks": data.get("totalMarks", 100)
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
        # print("Establising connection...")
        conn.request(
            "GET",
            f"/proctoring/session/{email}"
        )
        # print("getting response...")
        response = conn.getresponse()

        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.reason}")

        # print("getting data from response...")

        data = json.loads(response.read().decode("utf-8"))

        # print(f"original data: {data}")

        return {
            "sessionId": f"session_{email}",   # Remove if your API returns it
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