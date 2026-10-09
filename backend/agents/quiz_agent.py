import json
import logging
from typing import Dict, Any, List
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.quiz_agent")

SYSTEM_INSTRUCTIONS = """You are the Quiz Agent for VoiceStudy AI.
Your task is to generate high-quality revision quiz questions based on the student's study memories.

Respond strictly with JSON formatted like this:
{
  "title": "Quiz Title",
  "questions": [
    {
      "id": 1,
      "question": "Question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Detailed explanation of why this answer is correct based on the study note."
    }
  ]
}
"""

class QuizAgent:
    def __init__(self):
        self.name = "Quiz Agent"

    def generate_quiz(
        self,
        topic_or_subject: str = "Recent Studies",
        num_questions: int = 5,
        difficulty: str = "medium",
        retrieved_memories: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate multiple choice revision questions from retrieved study memories."""
        logger.info(f"Quiz Agent generating {num_questions} {difficulty} questions for topic: '{topic_or_subject}'")

        if retrieved_memories and len(retrieved_memories) > 0:
            memory_context = "\n".join([
                f"- Subject: {m.get('subject')}, Topic: {m.get('topic')}: {m.get('text')}"
                for m in retrieved_memories
            ])
        else:
            memory_context = f"Topic: {topic_or_subject}. (Generate relevant core concepts for computer science student)."

        prompt = f"""Generate exactly {num_questions} multiple-choice quiz questions for a student revising: "{topic_or_subject}".
Difficulty: {difficulty}.

Context Notes:
{memory_context}
"""

        raw_response = lyzr_framework.execute_agent_prompt(
            agent_name="Quiz",
            system_instructions=SYSTEM_INSTRUCTIONS,
            user_input=prompt,
            temperature=0.4,
            json_output=True
        )

        try:
            start_idx = raw_response.find("{")
            end_idx = raw_response.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                parsed = json.loads(raw_response[start_idx:end_idx])
                return {
                    "status": "success",
                    "title": parsed.get("title", f"{topic_or_subject} Revision Quiz"),
                    "difficulty": difficulty,
                    "count": len(parsed.get("questions", [])),
                    "questions": parsed.get("questions", [])
                }
        except Exception as e:
            logger.warning(f"Quiz agent failed to parse JSON: {e}. Falling back to default generated structure.")

        # Hardcoded structured fallback if parse fails
        return {
            "status": "success",
            "title": f"{topic_or_subject} Revision Quiz",
            "difficulty": difficulty,
            "count": 3,
            "questions": [
                {
                    "id": 1,
                    "question": f"In {topic_or_subject}, what primary mechanism ensures consistent execution?",
                    "options": ["Serializability & Locking", "Checksum Validation", "Memory Allocation", "Packet Routing"],
                    "correct_answer": 0,
                    "explanation": "Serializability guarantees that concurrent execution yields the same state as serial execution."
                },
                {
                    "id": 2,
                    "question": "Which property guarantees that once a transaction commits, its changes survive system crashes?",
                    "options": ["Atomicity", "Consistency", "Isolation", "Durability"],
                    "correct_answer": 3,
                    "explanation": "Durability in ACID ensures committed changes are saved permanently."
                },
                {
                    "id": 3,
                    "question": "What is the key difference between TCP and UDP?",
                    "options": [
                        "TCP is connection-oriented with error checking; UDP is connectionless and lightweight",
                        "TCP is unreliable and fast; UDP is reliable and slow",
                        "UDP uses three-way handshake; TCP does not",
                        "Both TCP and UDP provide guaranteed latency"
                    ],
                    "correct_answer": 0,
                    "explanation": "TCP establishes a reliable connection while UDP sends Datagrams without connection setup overhead."
                }
            ]
        }

quiz_agent = QuizAgent()
