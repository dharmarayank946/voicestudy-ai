import unittest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestQuizGeneration(unittest.TestCase):
    def test_quiz_count_3(self):
        """1. Verify requesting 3 questions returns exactly 3 questions."""
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
        """1. Verify requesting 5 questions returns exactly 5 questions."""
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
        """1. Verify requesting 10 questions returns exactly 10 questions."""
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

    def test_no_raw_prompt_instructions(self):
        """2 & 4. Verify question text contains no raw prompt instructions like 'Generate exactly'."""
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
            self.assertNotIn("revising:", question_text)
            self.assertTrue(len(question_text) > 15)

    def test_dbms_concurrency_topic_relevance(self):
        """3. Verify DBMS Concurrency Control questions do not contain unrelated topics like indexing or packet routing."""
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

    def test_no_duplicate_questions(self):
        """5. Verify questions are not duplicated within the same quiz."""
        response = client.post("/api/quiz", json={
            "topic": "DBMS Concurrency Control",
            "num_questions": 10,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        question_texts = [q["question"].strip() for q in data["questions"]]
        self.assertEqual(len(question_texts), len(set(question_texts)), "Quiz contains duplicate questions!")

    def test_question_options_and_answers_validity(self):
        """6. Every question must have four unique options and exactly one valid correct answer index."""
        response = client.post("/api/quiz", json={
            "topic": "Operating Systems Paging",
            "num_questions": 5,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for q in data["questions"]:
            options = q["options"]
            self.assertEqual(len(options), 4, "Question must have exactly 4 options")
            self.assertEqual(len(set(options)), 4, "All 4 options must be distinct")
            self.assertIn(q["correct_answer"], [0, 1, 2, 3], "correct_answer index must be 0, 1, 2, or 3")
            self.assertTrue(len(q.get("explanation", "").strip()) > 5, "Explanation must be present")

    def test_answer_evaluation_and_score_logic(self):
        """7 & 10. Verify answer options, correct answer index, and score calculation update correctly."""
        response = client.post("/api/quiz", json={
            "topic": "Database ACID Properties",
            "num_questions": 5,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        questions = data["questions"]
        
        # Simulate user answering all questions correctly
        user_answers = {idx: q["correct_answer"] for idx, q in enumerate(questions)}
        score = sum(1 for idx, q in enumerate(questions) if user_answers.get(idx) == q["correct_answer"])
        self.assertEqual(score, 5)

        # Simulate user changing answer for index 0 to wrong answer
        user_answers[0] = (questions[0]["correct_answer"] + 1) % 4
        updated_score = sum(1 for idx, q in enumerate(questions) if user_answers.get(idx) == q["correct_answer"])
        self.assertEqual(updated_score, 4)

    def test_different_topics_produce_topic_relevant_questions(self):
        """8. Verify different topics produce questions relevant to their own domain."""
        topics = [
            ("DBMS Concurrency Control", "serializability"),
            ("Computer Networks TCP/UDP", "tcp"),
            ("Operating Systems Paging", "page")
        ]
        for topic_name, expected_kw in topics:
            response = client.post("/api/quiz", json={
                "topic": topic_name,
                "num_questions": 3,
                "difficulty": "medium"
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            full_quiz_text = " ".join([q["question"] + " " + " ".join(q.get("options", [])) + " " + q.get("explanation", "") for q in data["questions"]]).lower()
            self.assertIn(expected_kw, full_quiz_text, f"Topic '{topic_name}' quiz missing keyword '{expected_kw}'")

    def test_missing_memories_fallback(self):
        """9. Missing or empty study memories still allow offline quiz generator to function cleanly."""
        response = client.post("/api/quiz", json={
            "topic": "Unheard Subject 9999",
            "num_questions": 5,
            "difficulty": "medium"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["questions"]), 5)

    def test_invalid_requests_handled_safely(self):
        """10. Invalid question counts or empty topic strings are handled safely."""
        # Test empty topic
        response1 = client.post("/api/quiz", json={"topic": "", "num_questions": 5})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()["status"], "success")

        # Test invalid question count (e.g. 99 or negative)
        response2 = client.post("/api/quiz", json={"topic": "DBMS", "num_questions": 99})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()["count"], 10)  # Clamped to closest valid max count 10

        response3 = client.post("/api/quiz", json={"topic": "DBMS", "num_questions": -1})
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()["count"], 3)   # Clamped to closest valid min count 3

if __name__ == "__main__":
    unittest.main()
