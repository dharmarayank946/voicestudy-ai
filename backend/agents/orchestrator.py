import json
import logging
from typing import Dict, Any
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.orchestrator")

SYSTEM_PROMPT = """You are the Orchestrator Agent for VoiceStudy AI, a voice-first study assistant.
Your job is to analyze the student's voice input or text prompt and classify the user's intent.

Respond strictly in JSON format with the following keys:
{
  "intent": "REMEMBER" | "RETRIEVE" | "EXPLAIN" | "QUIZ" | "SUMMARIZE",
  "subject": "Extracted Subject e.g. DBMS, Computer Networks, Operating Systems, Mathematics, or General",
  "topic": "Extracted Specific Topic e.g. Concurrency Control, TCP vs UDP, Page Replacement",
  "extracted_content": "Clean version of what the student studied or asked",
  "reasoning": "Brief explanation of intent choice"
}

Intent Classification Rules:
- REMEMBER: Student explicitly states what they studied, learned, read, or want stored (e.g. "Remember that...", "I studied...", "Save this...").
- RETRIEVE: Student asks what or when they studied a topic (e.g. "What did I study about...", "When did I read...").
- EXPLAIN: Student asks to explain, compare, or clarify concepts based on prior study (e.g. "Explain what I studied", "Compare TCP and UDP").
- QUIZ: Student asks for revision questions, flashcards, or tests (e.g. "Give me five revision questions", "Quiz me on...").
- SUMMARIZE: Student asks for a summary of studied topics or progress (e.g. "What topics have I studied recently?", "Summarize my study history").
"""

class OrchestratorAgent:
    def __init__(self):
        self.name = "Orchestrator Agent"

    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """Classify user intent and extract subject/topic metadata."""
        logger.info(f"Orchestrator analyzing prompt: {user_input[:80]}")
        
        raw_response = lyzr_framework.execute_agent_prompt(
            agent_name="Orchestrator",
            system_instructions=SYSTEM_PROMPT,
            user_input=user_input,
            temperature=0.1,
            json_output=True
        )

        try:
            # Parse JSON
            start_idx = raw_response.find("{")
            end_idx = raw_response.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = raw_response[start_idx:end_idx]
                parsed = json.loads(json_str)
                return {
                    "intent": parsed.get("intent", "RETRIEVE").upper(),
                    "subject": parsed.get("subject", "General"),
                    "topic": parsed.get("topic", "General Study"),
                    "extracted_content": parsed.get("extracted_content", user_input),
                    "reasoning": parsed.get("reasoning", "")
                }
        except Exception as e:
            logger.warning(f"Orchestrator failed to parse JSON response: {e}. Using fallback heuristic.")

        # Heuristic intent parser
        lower = user_input.lower()
        if any(kw in lower for kw in ["explain", "compare", "difference between", "how does", "what is"]):
            intent = "EXPLAIN"
        elif any(kw in lower for kw in ["summarize", "summary", "recent topics", "list topics", "overview"]):
            intent = "SUMMARIZE"
        elif any(kw in lower for kw in ["quiz", "question", "questions", "test me", "revision"]):
            intent = "QUIZ"
        elif any(kw in lower for kw in ["what did i", "when did i", "show my", "recall", "search"]):
            intent = "RETRIEVE"
        elif any(kw in lower for kw in ["remember", "note that", "save", "learned", "studied"]):
            intent = "REMEMBER"
        else:
            intent = "RETRIEVE"

        # Basic subject extraction
        subject = "General"
        if "dbms" in lower or "database" in lower or "sql" in lower or "concurrency" in lower:
            subject = "DBMS"
        elif "network" in lower or "tcp" in lower or "udp" in lower or "ip" in lower or "http" in lower:
            subject = "Computer Networks"
        elif "os" in lower or "operating system" in lower or "process" in lower or "paging" in lower:
            subject = "Operating Systems"

        topic = "Study Memory"
        if "concurrency" in lower:
            topic = "Concurrency Control"
        elif "tcp" in lower or "udp" in lower:
            topic = "TCP and UDP"

        return {
            "intent": intent,
            "subject": subject,
            "topic": topic,
            "extracted_content": user_input,
            "reasoning": "Rule-based fallback intent classification"
        }

orchestrator_agent = OrchestratorAgent()
