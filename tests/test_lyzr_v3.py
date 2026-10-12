import os
import unittest
from unittest.mock import patch, MagicMock
import httpx
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.lyzr_agent_framework import (
    LyzrAgentFramework,
    LyzrAPIError,
    LyzrTimeoutError
)

client = TestClient(app)

class TestLyzrV3Integration(unittest.TestCase):
    def test_01_framework_status_environment_variables(self):
        """Test reading LYZR_API_KEY, LYZR_AGENT_ID, LYZR_USER_ID, LYZR_CHAT_URL from environment."""
        with patch.dict(os.environ, {
            "LYZR_API_KEY": "lyzr-test-key-12345",
            "LYZR_AGENT_ID": "agent_test_999",
            "LYZR_USER_ID": "student_alpha",
            "LYZR_CHAT_URL": "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
        }):
            framework = LyzrAgentFramework()
            status = framework.get_framework_status()
            
            self.assertEqual(framework.lyzr_api_key, "lyzr-test-key-12345")
            self.assertEqual(framework.default_agent_id, "agent_test_999")
            self.assertEqual(framework.user_id, "student_alpha")
            self.assertEqual(framework.chat_url, "https://agent-prod.studio.lyzr.ai/v3/inference/chat/")
            self.assertTrue(status["is_real_ai"])
            self.assertEqual(status["mode"], "real_lyzr_api")
            self.assertTrue(status["lyzr_api_key_configured"])
            self.assertTrue(status["lyzr_agent_id_configured"])
            self.assertEqual(status["lyzr_user_id"], "student_alpha")

    def test_02_successful_lyzr_v3_chat_call(self):
        """Test execute_agent_prompt sends POST to V3 chat endpoint with required headers & payload."""
        with patch.dict(os.environ, {
            "LYZR_API_KEY": "lyzr-live-token",
            "LYZR_AGENT_ID": "agent_live_001",
            "LYZR_USER_ID": "user_student_101",
            "LYZR_CHAT_URL": "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
        }):
            framework = LyzrAgentFramework()
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "Strict Two-Phase Locking (2PL) guarantees serializability and prevents cascading aborts."
            }

            with patch("httpx.Client.post", return_value=mock_response) as mock_post:
                result = framework.execute_agent_prompt(
                    agent_name="Assistant",
                    system_instructions="You are a study tutor.",
                    user_input="Explain Strict 2PL from my study notes."
                )

                self.assertIn("Strict Two-Phase Locking", result)
                mock_post.assert_called_once()
                call_args, call_kwargs = mock_post.call_args
                
                # Verify URL
                self.assertEqual(call_args[0], "https://agent-prod.studio.lyzr.ai/v3/inference/chat/")
                
                # Verify Headers
                headers = call_kwargs["headers"]
                self.assertEqual(headers["x-api-key"], "lyzr-live-token")
                self.assertEqual(headers["Content-Type"], "application/json")
                
                # Verify Payload
                payload = call_kwargs["json"]
                self.assertEqual(payload["user_id"], "user_student_101")
                self.assertEqual(payload["agent_id"], "agent_live_001")
                self.assertIn("Explain Strict 2PL", payload["message"])

    def test_03_lyzr_api_error_raises_exception_without_substitution(self):
        """Test API errors (e.g. HTTP 401 or 500) raise LyzrAPIError without silently substituting unrelated answers."""
        with patch.dict(os.environ, {
            "LYZR_API_KEY": "lyzr-bad-token",
            "LYZR_AGENT_ID": "agent_live_001",
            "LYZR_USER_ID": "user_student_101"
        }):
            framework = LyzrAgentFramework()
            
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = '{"detail": "Invalid API key"}'

            with patch("httpx.Client.post", return_value=mock_response):
                with self.assertRaises(LyzrAPIError) as ctx:
                    framework.execute_agent_prompt(
                        agent_name="Assistant",
                        system_instructions="You are a tutor.",
                        user_input="What is Photosynthesis?"
                    )
                self.assertIn("401", str(ctx.exception))

    def test_04_lyzr_timeout_raises_exception_without_substitution(self):
        """Test timeout raises LyzrTimeoutError without silently substituting unrelated answers."""
        with patch.dict(os.environ, {
            "LYZR_API_KEY": "lyzr-live-token",
            "LYZR_AGENT_ID": "agent_live_001",
            "LYZR_USER_ID": "user_student_101"
        }):
            framework = LyzrAgentFramework()

            with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timeout")):
                with self.assertRaises(LyzrTimeoutError) as ctx:
                    framework.execute_agent_prompt(
                        agent_name="Assistant",
                        system_instructions="You are a tutor.",
                        user_input="Explain TCP 3-way handshake."
                    )
                self.assertIn("timed out", str(ctx.exception).lower())

    def test_05_study_endpoint_handles_lyzr_error_gracefully(self):
        """Test /api/study endpoint catches Lyzr errors and returns honest error payload without crashing."""
        with patch.dict(os.environ, {
            "LYZR_API_KEY": "lyzr-configured-key",
            "LYZR_AGENT_ID": "agent_live_001",
            "LYZR_USER_ID": "user_student_101"
        }):
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.text = '{"error": "Agent inference temporarily unavailable"}'

            with patch("httpx.Client.post", return_value=mock_response):
                res = client.post("/api/study", json={
                    "transcript": "Explain what I studied about operating systems.",
                    "source": "text_fallback",
                    "uid": "test_user_err"
                })
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertEqual(data.get("response_type"), "error")
                self.assertIn("Lyzr Agent Error", data.get("message", ""))
                self.assertIn("503", data.get("message", ""))

    def test_06_study_endpoint_returns_real_lyzr_response_with_qdrant_context(self):
        """Test /api/study passes retrieved Qdrant memories to Lyzr agent and returns Lyzr's actual response."""
        # 1. Save memory in Qdrant
        client.post("/api/study", json={
            "transcript": "Operating Systems: Virtual memory uses demand paging and page tables.",
            "source": "text_fallback",
            "subject_override": "Operating Systems",
            "topic_override": "Virtual Memory",
            "uid": "test_user_qdrant_lyzr"
        })

        # 2. Query with mock Lyzr API configured
        with patch.dict(os.environ, {
            "LYZR_API_KEY": "lyzr-valid-key",
            "LYZR_AGENT_ID": "agent_os_tutor",
            "LYZR_USER_ID": "student_os"
        }):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "Real Lyzr Response: Virtual memory maps virtual addresses to physical frames using page tables."
            }

            with patch("httpx.Client.post", return_value=mock_response) as mock_post:
                res = client.post("/api/study", json={
                    "transcript": "What did I study about virtual memory and paging?",
                    "source": "text_fallback",
                    "uid": "test_user_qdrant_lyzr"
                })
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertIn("Real Lyzr Response", data.get("message", ""))
                
                # Ensure Qdrant context was included in the message sent to Lyzr
                call_args, call_kwargs = mock_post.call_args
                payload = call_kwargs["json"]
                self.assertIn("RETRIEVED NOTEBOOK MEMORIES (FROM QDRANT VECTOR STORE)", payload["message"])
                self.assertEqual(payload["agent_id"], "agent_os_tutor")
                self.assertEqual(payload["user_id"], "student_os")

if __name__ == "__main__":
    unittest.main()
