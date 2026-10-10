import os
import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.lyzr_agent_framework import lyzr_framework
from backend.agents.orchestrator import orchestrator_agent
from backend.agents.assistant_agent import study_assistant_agent
from backend.agents.memory_agent import study_memory_agent

class TestAITutor(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_framework_status_reporting(self):
        status = lyzr_framework.get_framework_status()
        self.assertIn("mode", status)
        self.assertIn("is_real_ai", status)
        self.assertIn("provider_name", status)
        self.assertIn("notice", status)
        # Verify provider status contains honest label
        if not status["is_real_ai"]:
            self.assertEqual(status["provider_name"], "Offline Engine Fallback")

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

        # General Knowledge
        gen_res = orchestrator_agent.analyze_intent("Tell me how solar energy and photovoltaic panels function.")
        self.assertEqual(gen_res["intent"], "EXPLAIN")

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
        self.assertNotIn("Strict 2PL", data["message"])

    def test_consecutive_subject_switching_no_old_context_leakage(self):
        """Verify consecutive queries switching between subjects do not leak old context."""
        user_uid = "test_switching_user_101"

        # Q1: DBMS
        res1 = self.client.post("/api/study", json={
            "transcript": "Explain Strict 2PL locking in database concurrency.",
            "uid": user_uid,
            "source": "text_fallback"
        })
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["orchestration"]["subject"], "DBMS")
        self.assertIn("Two-Phase Locking", res1.json()["message"])

        # Q2: Operating Systems (Immediately after DBMS query)
        res2 = self.client.post("/api/study", json={
            "transcript": "Explain how virtual memory handles page faults.",
            "uid": user_uid,
            "source": "text_fallback"
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["orchestration"]["subject"], "Operating Systems")
        self.assertIn("Virtual Memory", res2.json()["message"])
        self.assertNotIn("Two-Phase Locking", res2.json()["message"])

        # Q3: Mathematics (Immediately after OS query)
        res3 = self.client.post("/api/study", json={
            "transcript": "Explain matrix multiplication in linear algebra.",
            "uid": user_uid,
            "source": "text_fallback"
        })
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(res3.json()["orchestration"]["subject"], "Mathematics")
        self.assertIn("Linear Algebra", res3.json()["message"])
        self.assertNotIn("Page Fault", res3.json()["message"])
        self.assertNotIn("Two-Phase Locking", res3.json()["message"])

        # Q4: Software Engineering
        res4 = self.client.post("/api/study", json={
            "transcript": "Explain the Single Responsibility Principle in SOLID design.",
            "uid": user_uid,
            "source": "text_fallback"
        })
        self.assertEqual(res4.status_code, 200)
        self.assertEqual(res4.json()["orchestration"]["subject"], "Software Engineering")
        self.assertIn("SOLID Principles", res4.json()["message"])
        self.assertNotIn("Linear Algebra", res4.json()["message"])

    def test_saved_memory_subject_isolation(self):
        """Verify saved DBMS notes are not force-attached to OS or Math queries."""
        user_uid = "test_memory_isolation_user_202"
        
        # Save a DBMS note
        save_res = study_memory_agent.save_study_memory(
            text="DBMS Strict 2PL holds all exclusive locks until transaction commit to prevent cascading aborts.",
            subject="DBMS",
            topic="Concurrency Control",
            uid=user_uid
        )
        self.assertEqual(save_res.get("status"), "success")

        # Query about OS - should NOT include the saved DBMS note
        os_res = self.client.post("/api/study", json={
            "transcript": "Explain virtual memory in Operating Systems.",
            "uid": user_uid,
            "source": "text_fallback"
        })
        self.assertEqual(os_res.status_code, 200)
        os_data = os_res.json()
        self.assertEqual(os_data["orchestration"]["subject"], "Operating Systems")
        self.assertNotIn("Strict 2PL", os_data["message"])
        self.assertNotIn("Saved Study Notebook Entries", os_data["message"])

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
