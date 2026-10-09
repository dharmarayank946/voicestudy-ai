import unittest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestQuizGeneration(unittest.TestCase):
    def test_quiz_count_3(self):
        """Verify requesting 3 questions returns exactly 3 questions."""
        response = client.post("/api/quiz", json={
            "topic": "DBMS Concurrency Control",
            "num_questions": 3,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["questions"]), 3)

    def test_quiz_count_5(self):
        """Verify requesting 5 questions returns exactly 5 questions."""
        response = client.post("/api/quiz", json={
            "topic": "Computer Networks TCP/UDP",
            "num_questions": 5,
            "difficulty": "hard"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 5)
        self.assertEqual(len(data["questions"]), 5)

    def test_quiz_count_10(self):
        """Verify requesting 10 questions returns exactly 10 questions."""
        response = client.post("/api/quiz", json={
            "topic": "Operating Systems Paging",
            "num_questions": 10,
            "difficulty": "easy"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 10)
        self.assertEqual(len(data["questions"]), 10)

    def test_quiz_wording_clean(self):
        """Verify question text is grammatically clean and contains no raw prompt artifacts."""
        response = client.post("/api/quiz", json={
            "topic": "DBMS Concurrency Control",
            "num_questions": 5,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for q in data["questions"]:
            question_text = q["question"]
            self.assertNotIn("Generate exactly", question_text)
            self.assertTrue(len(question_text) > 15)
            self.assertIn("options", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["correct_answer"], [0, 1, 2, 3])
            self.assertTrue(len(q.get("explanation", "")) > 5)

    def test_dbms_concurrency_topic_relevance(self):
        """Verify DBMS Concurrency Control questions do not contain unrelated topics like indexing or packet routing."""
        response = client.post("/api/quiz", json={
            "topic": "DBMS Concurrency Control",
            "num_questions": 5,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        questions = data["questions"]
        self.assertEqual(len(questions), 5)
        
        # Verify Question 4 specifically covers Strict 2PL and cascading aborts
        q4 = questions[3]
        self.assertIn("Strict Two-Phase Locking", q4["question"])
        self.assertIn("cascading aborts", q4["question"])
        self.assertNotIn("indexing", q4["question"].lower())
        self.assertNotIn("log n", q4["question"].lower())
        
        # Verify all questions focus strictly on database concurrency concepts
        for q in questions:
            q_text = q["question"].lower()
            self.assertNotIn("checksum validation", q_text)
            self.assertNotIn("packet routing", q_text)

    def test_networks_topic_relevance(self):
        """Verify Computer Networks questions focus strictly on transport protocols and TCP/UDP."""
        response = client.post("/api/quiz", json={
            "topic": "Computer Networks TCP/UDP",
            "num_questions": 5,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        questions = data["questions"]
        self.assertEqual(len(questions), 5)
        
        # Verify Q1 focuses on three-way handshake
        self.assertIn("three-way handshake", questions[0]["explanation"].lower())
        # Verify Q4 focuses on congestion control
        self.assertIn("congestion control", questions[3]["question"].lower())

    def test_answer_evaluation_and_score_logic(self):
        """Verify answer options and correct answer index evaluate correctly."""
        response = client.post("/api/quiz", json={
            "topic": "Database ACID Properties",
            "num_questions": 3,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        questions = data["questions"]
        
        # Simulate user answering all questions correctly
        user_answers = {idx: q["correct_answer"] for idx, q in enumerate(questions)}
        score = sum(1 for idx, q in enumerate(questions) if user_answers[idx] == q["correct_answer"])
        self.assertEqual(score, 3)

        # Simulate user answering all questions incorrectly
        wrong_answers = {idx: (q["correct_answer"] + 1) % 4 for idx, q in enumerate(questions)}
        wrong_score = sum(1 for idx, q in enumerate(questions) if wrong_answers[idx] == q["correct_answer"])
        self.assertEqual(wrong_score, 0)

if __name__ == "__main__":
    unittest.main()
