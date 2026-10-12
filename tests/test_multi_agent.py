import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.agents.summarizer_agent import summarizer_agent, SummarizerAgent
from backend.agents.action_item_agent import action_item_agent, ActionItemExtractorAgent
from backend.agents.assistant_agent import memory_assistant_agent, study_assistant_agent
from backend.agents.manager_agent import manager_agent, ManagerAgent
from backend.services.lyzr_agent_framework import lyzr_framework, LyzrAPIError, LyzrTimeoutError

client = TestClient(app)

class TestMultiAgentOrchestration(unittest.TestCase):
    def setUp(self):
        self.sample_meeting_transcript = (
            "Alex: Welcome everyone. In today's standup, we decided to migrate our persistent vector storage "
            "to Qdrant Cloud cluster by Friday. Sarah will handle the webhook payload formatting from the Omi device. "
            "David is assigned to write the integration tests for the Lyzr V3 chat API endpoint by tomorrow 5 PM. "
            "We also agreed that frontend credentials must never be exposed."
        )

    def test_01_summarizer_agent_execution(self):
        """Test Summarizer Agent summarizes meeting and lecture transcripts into key points."""
        result = summarizer_agent.summarize_transcript(self.sample_meeting_transcript)
        self.assertIn("summary", result)
        self.assertEqual(result["agent_executed"], "Summarizer Agent")
        self.assertTrue(len(result["summary"]) > 50)
        self.assertTrue(any(k in result["summary"].lower() for k in ["summary", "key points", "standup", "qdrant"]))

    def test_02_action_item_agent_execution(self):
        """Test Action Item Extractor Agent extracts tasks, owners, and deadlines without hallucination."""
        result = action_item_agent.extract_action_items(self.sample_meeting_transcript)
        self.assertIn("action_items", result)
        self.assertEqual(result["agent_executed"], "Action Item Extractor Agent")
        self.assertTrue(len(result["action_items"]) > 50)
        self.assertTrue(any(k in result["action_items"].lower() for k in ["action item", "task", "deadline", "sarah", "david"]))

    def test_03_memory_assistant_agent_qdrant_grounding(self):
        """Test Memory Assistant Agent answers user questions using relevant memories retrieved from Qdrant."""
        mock_memories = [
            {
                "subject": "DBMS",
                "topic": "Concurrency Control",
                "text": "Strict 2PL retains all exclusive locks until transaction commit to prevent cascading aborts.",
                "score": 0.95
            }
        ]
        result = memory_assistant_agent.answer_question(
            user_query="How does Strict 2PL prevent cascading aborts?",
            retrieved_memories=mock_memories
        )
        self.assertIn("answer", result)
        self.assertTrue(len(result["answer"]) > 50)
        self.assertEqual(result["retrieved_memories_count"], 1)

    def test_04_manager_agent_delegates_to_action_items(self):
        """Test Manager Agent identifies action items request and delegates to Action Item Extractor Agent."""
        res = client.post("/api/study", json={
            "transcript": "Extract all action items, tasks, and deadlines from today's sprint meeting: Alex will complete frontend by Friday.",
            "source": "text_fallback"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "ACTION_ITEMS")
        self.assertEqual(data.get("agent_executed"), "Action Item Extractor Agent")
        self.assertEqual(data.get("response_type"), "action_items")
        self.assertTrue(any(k in data.get("message", "").lower() for k in ["action item", "task", "alex", "deadline"]))

    def test_05_manager_agent_multi_agent_coordination(self):
        """Test Manager Agent coordinates multiple agents (Summarizer + Action Items) in one clear answer."""
        res = client.post("/api/study", json={
            "transcript": (
                "Please summarize this meeting and extract all action items and deadlines: " + self.sample_meeting_transcript
            ),
            "source": "text_fallback"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "MULTI_AGENT")
        self.assertIn("Manager Agent", data.get("agent_executed"))
        self.assertIn("Summarizer Agent", data.get("agent_executed"))
        self.assertIn("Action Item Extractor Agent", data.get("agent_executed"))
        self.assertEqual(data.get("response_type"), "multi_agent_summary")
        # Output combines both summary and action items
        message = data.get("message", "")
        self.assertIn("Meeting & Lecture Summary", message)
        self.assertIn("Extracted Action Items & Decisions", message)

    def test_06_framework_status_tracks_multi_agent_configuration(self):
        """Test that get_framework_status tracks configured agent IDs and multi-agent availability."""
        status = lyzr_framework.get_framework_status()
        self.assertIn("configured_agent_ids", status)
        self.assertIn("Manager", status["configured_agent_ids"])
        self.assertIn("Summarizer", status["configured_agent_ids"])
        self.assertIn("Action Items", status["configured_agent_ids"])
        self.assertIn("Memory Assistant", status["configured_agent_ids"])
        self.assertIn("multi_agent_orchestration_active", status)

    def test_07_real_lyzr_routing_with_specialized_agent_ids(self):
        """Test that Lyzr execute_agent_prompt sends specific agent ID when configured in env."""
        with patch.dict("os.environ", {
            "LYZR_API_KEY": "test_real_key_abc",
            "LYZR_AGENT_ID": "default_shared_agent_id",
            "LYZR_AGENT_ID_SUMMARIZER": "specialized_summarizer_123"
        }):
            # Summarizer should get specialized ID
            self.assertEqual(lyzr_framework.get_agent_id("Summarizer"), "specialized_summarizer_123")
            # Action Items should safely fall back to default shared agent ID (free-tier single agent support)
            self.assertEqual(lyzr_framework.get_agent_id("Action Items"), "default_shared_agent_id")

    def test_08_manager_handles_lyzr_error_gracefully(self):
        """Test that Manager Agent propagates Lyzr API error cleanly without crashing or exposing secrets."""
        with patch("backend.services.lyzr_agent_framework.lyzr_framework.execute_agent_prompt",
                   side_effect=LyzrAPIError("Lyzr API returned HTTP 500: Internal Server Error")):
            res = client.post("/api/study", json={
                "transcript": "Extract action items and summary from this session.",
                "source": "text_fallback"
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data.get("response_type"), "error")
            self.assertIn("Lyzr Agent Error", data.get("message", ""))
            self.assertNotIn("test_real_key_abc", data.get("message", ""))


if __name__ == "__main__":
    unittest.main()
