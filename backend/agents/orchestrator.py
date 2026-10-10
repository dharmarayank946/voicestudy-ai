import json
import logging
from typing import Dict, Any, List, Optional
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.orchestrator")

SYSTEM_PROMPT = """You are the Orchestrator Agent for VoiceStudy AI, a voice-first AI study assistant.
Analyze the user's voice transcript or text prompt and optional conversation history to classify intent and extract metadata.

Respond strictly in JSON format with keys:
{
  "intent": "REMEMBER" | "RETRIEVE" | "EXPLAIN" | "QUIZ" | "SUMMARIZE",
  "subject": "Extracted Subject e.g. Software Engineering, Operating Systems, DBMS, Computer Networks, Programming, Mathematics, or General",
  "topic": "Extracted Specific Topic e.g. Virtual Memory, SOLID Principles, TCP vs UDP, Concurrency Control",
  "extracted_content": "Clean prompt text",
  "reasoning": "Reason for classification"
}
"""

class OrchestratorAgent:
    def __init__(self):
        self.name = "Orchestrator Agent"

    def analyze_intent(self, user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        logger.info(f"Orchestrator analyzing prompt: {user_input[:80]}")

        context_prompt = user_input
        if history:
            recent_turns = history[-4:]
            history_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in recent_turns])
            context_prompt = f"RECENT CONVERSATION HISTORY:\n{history_text}\n\nCURRENT USER PROMPT: {user_input}"

        raw_response = lyzr_framework.execute_agent_prompt(
            agent_name="Orchestrator",
            system_instructions=SYSTEM_PROMPT,
            user_input=context_prompt,
            temperature=0.1,
            json_output=True
        )

        try:
            start_idx = raw_response.find("{")
            end_idx = raw_response.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                parsed = json.loads(raw_response[start_idx:end_idx])
                return {
                    "intent": parsed.get("intent", "EXPLAIN").upper(),
                    "subject": parsed.get("subject", "General Study"),
                    "topic": parsed.get("topic", "General Concept"),
                    "extracted_content": parsed.get("extracted_content", user_input),
                    "reasoning": parsed.get("reasoning", "")
                }
        except Exception as e:
            logger.warning(f"Orchestrator JSON parse fallback: {e}")

        lower = user_input.lower()
        if any(kw in lower for kw in ["explain", "compare", "difference between", "how does", "what is", "describe", "why"]):
            intent = "EXPLAIN"
        elif any(kw in lower for kw in ["summarize", "summary", "recent topics", "list topics", "overview"]):
            intent = "SUMMARIZE"
        elif any(kw in lower for kw in ["quiz", "test", "question", "questions", "test me", "revision"]):
            intent = "QUIZ"
        elif any(kw in lower for kw in ["what did i", "when did i", "show my", "recall", "search"]):
            intent = "RETRIEVE"
        elif any(kw in lower for kw in ["remember", "note that", "save", "learned", "studied"]):
            intent = "REMEMBER"
        else:
            intent = "EXPLAIN"

        subject = "General Study"
        if any(k in lower for k in ["math", "calculus", "linear algebra", "matrix", "vector", "probability"]):
            subject = "Mathematics"
        elif any(k in lower for k in ["solid", "design pattern", "agile", "software engineering", "microservices"]):
            subject = "Software Engineering"
        elif any(k in lower for k in ["operating system", "paging", "process", "thread", "deadlock", "virtual memory"]):
            subject = "Operating Systems"
        elif any(k in lower for k in ["dbms", "database", "sql", "concurrency", "2pl", "acid"]):
            subject = "DBMS"
        elif any(k in lower for k in ["network", "tcp", "udp", "ip address", "tcp/ip", "protocol", "dns", "http"]):
            subject = "Computer Networks"
        elif any(k in lower for k in ["python", "java", "c++", "programming", "data structure", "algorithm", "async"]):
            subject = "Programming"

        topic = "General Concept"
        if "concurrency" in lower: topic = "Concurrency Control"
        elif "paging" in lower or "virtual memory" in lower: topic = "Virtual Memory & Paging"
        elif "tcp" in lower or "udp" in lower: topic = "TCP vs UDP"
        elif "solid" in lower: topic = "SOLID Principles"

        return {
            "intent": intent,
            "subject": subject,
            "topic": topic,
            "extracted_content": user_input,
            "reasoning": "Rule-based heuristic intent classification"
        }

orchestrator_agent = OrchestratorAgent()
