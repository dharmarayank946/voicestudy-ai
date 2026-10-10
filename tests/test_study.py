import unittest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestStudyFeature(unittest.TestCase):
    def test_01_remember_intent_saves_to_qdrant(self):
        """1. Test entering study notes with REMEMBER intent saves to Qdrant memory."""
        res = client.post("/api/study", json={
            "transcript": "Remember that I studied Strict 2PL protocol in DBMS today.",
            "source": "web_speech",
            "uid": "study_user_test_1"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "REMEMBER")
        self.assertEqual(data.get("agent_executed"), "Study Memory Agent")
        self.assertEqual(data.get("response_type"), "memory_saved")
        self.assertIn("Saved study note", data.get("message", ""))
        self.assertIsNotNone(data.get("data", {}).get("memory", {}).get("id"))

    def test_02_explain_intent_returns_grounded_answer(self):
        """2. Test EXPLAIN / RETRIEVE intent produces topic-relevant answer grounded in memories."""
        # First save a memory
        client.post("/api/study", json={
            "transcript": "Strict 2PL retains all exclusive locks until transaction commits or aborts.",
            "source": "text_fallback",
            "subject_override": "DBMS",
            "topic_override": "Concurrency Control",
            "uid": "study_user_test_1"
        })

        # Ask question
        res = client.post("/api/study", json={
            "transcript": "Explain what I studied about Strict 2PL locks.",
            "source": "text_fallback",
            "uid": "study_user_test_1"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data.get("intent"), ["EXPLAIN", "RETRIEVE"])
        self.assertEqual(data.get("agent_executed"), "Study Assistant Agent")
        self.assertTrue(len(data.get("message", "")) > 20)
        self.assertNotIn("Generate exactly", data.get("message", ""))

    def test_03_quiz_intent_returns_questions(self):
        """3. Test QUIZ intent generates revision questions without prompt leakage."""
        res = client.post("/api/study", json={
            "transcript": "Give me five revision questions on DBMS Concurrency Control.",
            "source": "text_fallback",
            "uid": "study_user_test_1"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "QUIZ")
        self.assertEqual(data.get("agent_executed"), "Quiz Agent")
        quiz_data = data.get("data", {})
        questions = quiz_data.get("questions", [])
        self.assertTrue(len(questions) > 0)
        for q in questions:
            self.assertNotIn("Generate exactly", q["question"])

    def test_04_summarize_intent(self):
        """4. Test SUMMARIZE intent returns study timeline overview."""
        res = client.post("/api/study", json={
            "transcript": "Summarize what I studied recently.",
            "source": "text_fallback",
            "uid": "study_user_test_1"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "SUMMARIZE")
        self.assertEqual(data.get("agent_executed"), "Study Memory Agent")
        self.assertTrue(len(data.get("message", "")) > 10)

    def test_05_empty_input_validation(self):
        """5. Test empty transcript input returns 400 Bad Request error."""
        res = client.post("/api/study", json={
            "transcript": "   ",
            "source": "text_fallback"
        })
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["detail"], "Voice or text input transcript cannot be empty.")

if __name__ == "__main__":
    unittest.main()