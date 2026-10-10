import unittest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestDashboardSettingsFeature(unittest.TestCase):
    def test_01_health_check_endpoint(self):
        """1. Verify system health check returns accurate connectivity and service status."""
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "VoiceStudy AI")
        self.assertEqual(data.get("version"), "1.0.0")

        # Verify vector memory status block
        v_mem = data.get("vector_memory", {})
        self.assertEqual(v_mem.get("status"), "connected")
        self.assertEqual(v_mem.get("provider"), "Qdrant")
        self.assertIn("total_memories", v_mem)
        self.assertEqual(v_mem.get("vector_dimension"), 1536)

        # Verify agents status block
        agents = data.get("agents", {})
        self.assertEqual(agents.get("orchestrator"), "active")
        self.assertEqual(agents.get("study_memory_agent"), "active")
        self.assertEqual(agents.get("study_assistant_agent"), "active")
        self.assertEqual(agents.get("quiz_agent"), "active")

        # Verify voice adapter status block
        voice = data.get("voice", {})
        self.assertTrue(voice.get("fallback_active"))
        self.assertIn("web_speech_api", voice.get("supported_sources", []))

    def test_02_memory_stats_endpoint(self):
        """2. Verify memory stats endpoint returns structured counts and lists."""
        res = client.get("/api/memory/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_memories", data)
        self.assertIn("total_subjects", data)
        self.assertIn("total_topics", data)
        self.assertIn("subjects_list", data)
        self.assertIn("topics_list", data)
        self.assertIn("storage_mode", data)
        self.assertEqual(data.get("vector_dimension"), 1536)

    def test_03_data_consistency_between_health_and_stats(self):
        """3. Verify data consistency between health endpoint and stats endpoint."""
        h_res = client.get("/api/health")
        s_res = client.get("/api/memory/stats")
        
        self.assertEqual(h_res.status_code, 200)
        self.assertEqual(s_res.status_code, 200)
        
        h_count = h_res.json()["vector_memory"]["total_memories"]
        s_count = s_res.json()["total_memories"]
        self.assertEqual(h_count, s_count)

    def test_04_invalid_route_404_handling(self):
        """4. Verify non-existent routes return HTTP 404 status."""
        res = client.get("/api/nonexistent_route_99")
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()