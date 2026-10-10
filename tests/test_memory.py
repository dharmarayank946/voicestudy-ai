import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.memory.qdrant_service import memory_service

client = TestClient(app)

class TestMemoryFeature(unittest.TestCase):
    def test_01_save_memory_and_verify_in_recent(self):
        """1. Test saving a study memory and confirming it appears in recent memories."""
        save_response = client.post("/api/memory/save", json={
            "text": "Deadlock prevention in OS uses Bankers algorithm to ensure safe state allocation.",
            "subject": "Operating Systems",
            "topic": "Bankers Algorithm",
            "uid": "test_user_alpha"
        })
        self.assertEqual(save_response.status_code, 200)
        data = save_response.json()
        memory_id = data.get("id")
        self.assertIsNotNone(memory_id)
        self.assertEqual(data.get("subject"), "Operating Systems")
        self.assertEqual(data.get("topic"), "Bankers Algorithm")

        # Verify memory appears in recent memories
        recent_response = client.get("/api/memory/recent?uid_filter=test_user_alpha")
        self.assertEqual(recent_response.status_code, 200)
        recent_memories = recent_response.json().get("memories", [])
        self.assertTrue(any(m["id"] == memory_id for m in recent_memories), "Saved memory missing from recent list")

        # Clean up test memory
        client.delete(f"/api/memory/{memory_id}")

    def test_02_search_memories_by_topic(self):
        """2. Test searching memories by topic and confirming relevant results appear."""
        # Save a unique topic memory
        save_response = client.post("/api/memory/save", json={
            "text": "Sliding window protocol regulates TCP flow control between sender and receiver.",
            "subject": "Computer Networks",
            "topic": "TCP Flow Control",
            "uid": "test_user_alpha"
        })
        self.assertEqual(save_response.status_code, 200)
        memory_id = save_response.json()["id"]

        # Search by relevant topic keyword
        search_response = client.post("/api/memory/search", json={
            "query": "TCP sliding window flow control",
            "uid_filter": "test_user_alpha"
        })
        self.assertEqual(search_response.status_code, 200)
        results = search_response.json().get("results", [])
        self.assertTrue(len(results) > 0)
        self.assertTrue(any(r["id"] == memory_id for r in results), "Relevant memory not returned in search results")

        # Clean up
        client.delete(f"/api/memory/{memory_id}")

    def test_03_delete_memory_and_verify_removal(self):
        """3. Test deleting a memory and confirming it disappears from search and recent memories."""
        save_res = client.post("/api/memory/save", json={
            "text": "Temporary note to be deleted after testing.",
            "subject": "Testing",
            "topic": "Deletion Test",
            "uid": "test_user_alpha"
        })
        memory_id = save_res.json()["id"]

        # Delete the memory
        del_res = client.delete(f"/api/memory/{memory_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(del_res.json()["status"], "success")

        # Confirm removal from recent memories
        recent_res = client.get("/api/memory/recent?uid_filter=test_user_alpha")
        recent_memories = recent_res.json().get("memories", [])
        self.assertFalse(any(m["id"] == memory_id for m in recent_memories), "Deleted memory still present in recent list")

        # Confirm removal from search
        search_res = client.post("/api/memory/search", json={
            "query": "Temporary note to be deleted",
            "uid_filter": "test_user_alpha"
        })
        search_results = search_res.json().get("results", [])
        self.assertFalse(any(r["id"] == memory_id for r in search_results), "Deleted memory still returned in search")

    def test_04_user_isolation(self):
        """4. Verify memories are isolated between users."""
        user1_uid = "user_student_101"
        user2_uid = "user_student_202"

        # Save memory for user1
        save1 = client.post("/api/memory/save", json={
            "text": "User 1 private study note regarding Quantum Computing principles.",
            "subject": "Physics",
            "topic": "Quantum Mechanics",
            "uid": user1_uid
        })
        mem1_id = save1.json()["id"]

        # Search memories for user2 using user1's topic
        search_user2 = client.post("/api/memory/search", json={
            "query": "Quantum Computing principles",
            "uid_filter": user2_uid
        })
        self.assertEqual(search_user2.status_code, 200)
        results_user2 = search_user2.json().get("results", [])
        self.assertFalse(any(r["id"] == mem1_id for r in results_user2), "User 1 memory leaked to User 2 search")

        # Verify recent memories for user2 does not contain user1's memory
        recent_user2 = client.get(f"/api/memory/recent?uid_filter={user2_uid}")
        memories_user2 = recent_user2.json().get("memories", [])
        self.assertFalse(any(m["id"] == mem1_id for m in memories_user2), "User 1 memory leaked to User 2 recent list")

        # Clean up
        client.delete(f"/api/memory/{mem1_id}")

    def test_05_input_validation_and_error_handling(self):
        """5. Test input validation error handling."""
        # Empty text on save -> 400 Bad Request
        empty_save = client.post("/api/memory/save", json={"text": "", "subject": "DBMS"})
        self.assertEqual(empty_save.status_code, 400)

        # Empty search query -> 400 Bad Request
        empty_search = client.post("/api/memory/search", json={"query": "  "})
        self.assertEqual(empty_search.status_code, 400)

if __name__ == "__main__":
    unittest.main()