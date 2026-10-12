import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.memory.qdrant_service import memory_service
from backend.agents.memory_agent import study_memory_agent

client = TestClient(app)

class TestBackendAccuracyAndFiltering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        memory_service._ensure_active_client()

    def test_01_photosynthesis_general_question_without_memories(self):
        """
        Requirement A:
        When asking a general educational question (such as how photosynthesis works)
        without relevant saved memories, the assistant must NOT refuse to explain,
        must answer from knowledge, must NOT claim the user studied it,
        and retrieved_memories must be empty.
        """
        response = client.post("/api/study", json={
            "transcript": "How does photosynthesis work in green plants?",
            "source": "text_fallback",
            "uid": "test_photosynthesis_student_901"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        message = data.get("message", "")

        # Verify the tutor answered with photosynthesis content
        self.assertTrue(
            any(k in message.lower() for k in ["photosynthesis", "chlorophyll", "light", "glucose", "plant"]),
            f"Expected explanation of photosynthesis, got: {message[:200]}"
        )

        # Must not refuse
        self.assertNotIn("refuse", message.lower())
        self.assertNotIn("saved memories do not contain", message.lower())

        # Must not invent or claim prior study notes when none matched
        self.assertNotIn("Saved Study Notebook Entries", message)

        # Retrieved memories returned to client must be empty
        retrieved_memories = data.get("retrieved_memories", [])
        self.assertEqual(len(retrieved_memories), 0, "No unrelated memories should leak as retrieved context")

    def test_02_python_only_search_no_dbms_leakage(self):
        """
        Requirement B & C:
        Searching 'Python' must return Python-related materials only.
        Unrelated subjects like DBMS and Networks must NOT appear in Python search results.
        """
        user_uid = "test_python_search_user_902"

        # Save one Python note and one DBMS note for this user
        py_mem = memory_service.save_memory(
            text="Python functions use def keyword and return values to the caller.",
            subject="Python Programming",
            topic="Python Functions",
            uid=user_uid
        )
        db_mem = memory_service.save_memory(
            text="Strict Two-Phase Locking holds exclusive locks until transaction commit.",
            subject="DBMS",
            topic="Concurrency Control",
            uid=user_uid
        )

        try:
            # Search for 'Python' with subject_filter=None (global search for this user)
            res = client.post("/api/memory/search", json={
                "query": "Python",
                "uid_filter": user_uid,
                "limit": 5
            })
            self.assertEqual(res.status_code, 200)
            search_data = res.json()
            results = search_data.get("results", [])

            self.assertTrue(len(results) > 0, "Python search should return the Python note")
            for r in results:
                self.assertIn("python", (r.get("subject", "") + " " + r.get("topic", "") + " " + r.get("text", "")).lower())
                self.assertNotIn("strict 2pl", r.get("text", "").lower())
                self.assertNotEqual(r.get("subject"), "DBMS", "DBMS note must not leak into Python search results")
        finally:
            memory_service.delete_memory(py_mem["id"])
            memory_service.delete_memory(db_mem["id"])

    def test_03_dbms_only_filtering_and_empty_state_on_unrelated_query(self):
        """
        Requirement B:
        Selecting DBMS must show DBMS-related materials only.
        Searching an unrelated query (like 'Python' or 'photosynthesis') under DBMS
        must return an empty result state rather than leaking DBMS notes.
        """
        user_uid = "test_dbms_filter_user_903"

        db_mem = memory_service.save_memory(
            text="In DBMS, ACID properties guarantee reliable database transaction processing.",
            subject="DBMS",
            topic="ACID Properties",
            uid=user_uid
        )
        net_mem = memory_service.save_memory(
            text="TCP uses three-way handshake SYN SYN-ACK ACK to establish reliable streams.",
            subject="Computer Networks",
            topic="TCP Handshake",
            uid=user_uid
        )

        try:
            # 1. Fetch recent memories with subject_filter='DBMS'
            recent_res = client.get(f"/api/memory/recent?uid_filter={user_uid}&subject_filter=DBMS")
            self.assertEqual(recent_res.status_code, 200)
            recent_mems = recent_res.json().get("memories", [])
            self.assertTrue(len(recent_mems) > 0)
            for m in recent_mems:
                self.assertEqual(m.get("subject"), "DBMS")
                self.assertNotEqual(m.get("subject"), "Computer Networks")

            # 2. Search 'Python' while subject_filter is set to 'DBMS' -> must be empty state!
            unrelated_search = client.post("/api/memory/search", json={
                "query": "Python programming functions",
                "subject_filter": "DBMS",
                "uid_filter": user_uid
            })
            self.assertEqual(unrelated_search.status_code, 200)
            unrelated_results = unrelated_search.json().get("results", [])
            self.assertEqual(len(unrelated_results), 0, "Unrelated query under DBMS filter must yield 0 results")
        finally:
            memory_service.delete_memory(db_mem["id"])
            memory_service.delete_memory(net_mem["id"])

    def test_04_unrelated_memory_leakage_rejection_in_study_answers(self):
        """
        Requirement C:
        When user has DBMS memories saved, asking about an unrelated topic
        (e.g., Photosynthesis or Matrix multiplication) must NOT use the DBMS memory
        as supporting context or return it in retrieved_memories.
        """
        user_uid = "test_leakage_rejection_user_904"

        db_mem = memory_service.save_memory(
            text="Deadlock detection algorithm uses wait-for graphs to spot circular wait cycles.",
            subject="DBMS",
            topic="Deadlock Handling",
            uid=user_uid
        )

        try:
            res = client.post("/api/study", json={
                "transcript": "Explain how photosynthesis converts light into glucose.",
                "source": "text_fallback",
                "uid": user_uid
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()

            # Message must not contain DBMS deadlock notes
            self.assertNotIn("Deadlock detection", data.get("message", ""))
            self.assertNotIn("wait-for graph", data.get("message", "").lower())

            # Retrieved memories must be empty
            self.assertEqual(len(data.get("retrieved_memories", [])), 0)
        finally:
            memory_service.delete_memory(db_mem["id"])

    def test_05_user_uid_isolation_enforced(self):
        """
        Requirement B:
        Preserve user UID isolation and do not weaken access filtering.
        User A's notes must NEVER be visible or retrieved for User B.
        """
        uid_A = "uid_isolated_alice_555"
        uid_B = "uid_isolated_bob_777"

        mem_A = memory_service.save_memory(
            text="Alice's confidential research notes on Quantum Encryption algorithms.",
            subject="Physics",
            topic="Quantum Encryption",
            uid=uid_A
        )

        try:
            # Bob searches for Alice's topic with Bob's UID filter
            bob_search = client.post("/api/memory/search", json={
                "query": "Quantum Encryption algorithms",
                "uid_filter": uid_B
            })
            self.assertEqual(bob_search.status_code, 200)
            bob_results = bob_search.json().get("results", [])
            self.assertFalse(any(r["id"] == mem_A["id"] for r in bob_results), "User A memory leaked to User B search")

            # Bob requests recent memories with Bob's UID filter
            bob_recent = client.get(f"/api/memory/recent?uid_filter={uid_B}")
            self.assertEqual(bob_recent.status_code, 200)
            bob_recent_mems = bob_recent.json().get("memories", [])
            self.assertFalse(any(m["id"] == mem_A["id"] for m in bob_recent_mems), "User A memory leaked to User B recent list")
        finally:
            memory_service.delete_memory(mem_A["id"])

if __name__ == "__main__":
    unittest.main()
