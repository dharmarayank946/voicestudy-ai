import os
import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.lyzr_agent_framework import lyzr_framework
from backend.agents.orchestrator import orchestrator_agent
from backend.agents.assistant_agent import study_assistant_agent

class TestAITutor(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_framework_status_reporting(self):
        status = lyzr_framework.get_framework_status()
        self.assertIn("mode", status)
        self.assertIn("is_real_ai", status)
        self.assertIn("provider_name", status)
        self.assertIn("notice", status)

    def test_multi_subject_intent_classification(self):
        # Software Engineering
        se_res = orchestrator_agent.analyze_intent("What are the SOLID design principles in software engineering?")
        self.assertEqual(se_res["subject"], "Software Engineering")
        self.assertEqual(se_res["intent"], "EXPLAIN")

        # Operating Systems
        os_res = orchestrator_agent.analyze_intent("Explain how virtual memory and page faults work in operating systems.")
        self.assertEqual(os_res["subject"], "Operating Systems")
        self.assertEqual(os_res["intent"], "EXPLAIN")

        # Computer Networks
        net_res = orchestrator_agent.analyze_intent("Compare TCP vs UDP transport layer protocols.")
        self.assertEqual(net_res["subject"], "Computer Networks")
        self.assertEqual(net_res["intent"], "EXPLAIN")

        # DBMS
        db_res = orchestrator_agent.analyze_intent("How does strict two phase locking prevent cascading aborts in database concurrency?")
        self.assertEqual(db_res["subject"], "DBMS")
        self.assertEqual(db_res["intent"], "EXPLAIN")

        # Mathematics
        math_res = orchestrator_agent.analyze_intent("Explain the concept of linear algebra matrix vector multiplication in computer science.")
        self.assertEqual(math_res["subject"], "Mathematics")
        self.assertEqual(math_res["intent"], "EXPLAIN")

    def test_subject_leakage_prevention(self):
        """Verify OS questions receive OS answers instead of default DBMS notes."""
        response = self.client.post("/api/study", json={
            "transcript": "Explain virtual memory and page faults in Operating Systems.",
            "source": "text_fallback"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["orchestration"]["subject"], "Operating Systems")
        self.assertIn("Virtual Memory", data["message"])
        self.assertNotIn("Two-Phase Locking", data["message"])

    def test_conversation_context_followup(self):
        """Verify follow-up questions incorporate conversation history."""
        history = [
            {"role": "user", "content": "What is an Operating System?"},
            {"role": "assistant", "content": "An Operating System manages hardware resources and software process execution."}
        ]
        response = self.client.post("/api/study", json={
            "transcript": "What are its main functions?",
            "history": history,
            "source": "text_fallback"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "EXPLAIN")
        self.assertIn("ai_provider", data)

    def test_empty_transcript_rejection(self):
        response = self.client.post("/api/study", json={
            "transcript": "   ",
            "source": "web_speech"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot be empty", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
