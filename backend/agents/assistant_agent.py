import logging
from typing import Dict, Any, List, Optional
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.assistant_agent")

SYSTEM_INSTRUCTIONS = """You are the Study Assistant Agent for VoiceStudy AI, behaving like an intelligent AI tutor (ChatGPT-style).
Your goal is to provide clear, engaging, correct explanations for student questions across any subject (Software Engineering, OS, DBMS, Networks, Mathematics, Programming, General).

Guidelines:
1. Explain concepts clearly using simple English, structured markdown, bold headers, bullet points, and practical examples.
2. If relevant study memories are provided, cite them clearly under a 'Saved Study Notebook Entries' header.
3. If no study memories exist or if they are on an unrelated subject, answer the question accurately directly from subject knowledge. Do not invent fake memories or force unrelated subjects.
4. Keep answers helpful, concise, and structured for quick revision.
"""

class StudyAssistantAgent:
    def __init__(self):
        self.name = "Study Assistant Agent"

    def answer_question(
        self,
        user_query: str,
        retrieved_memories: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        logger.info(f"Study Assistant generating answer for: '{user_query[:60]}'")

        relevant_memories = []
        if retrieved_memories:
            q_words = set(user_query.lower().split())
            for m in retrieved_memories:
                m_txt = (m.get("text", "") + " " + m.get("subject", "") + " " + m.get("topic", "")).lower()
                m_words = set(m_txt.split())
                overlap = len(q_words.intersection(m_words))
                if overlap >= 1 or len(retrieved_memories) == 1:
                    relevant_memories.append(m)

        context_str = ""
        if relevant_memories:
            context_items = []
            for idx, m in enumerate(relevant_memories, 1):
                sub = m.get("subject", "General")
                top = m.get("topic", "Topic")
                txt = m.get("text", "")
                context_items.append(f"Memory #{idx} [{sub} - {top}]:\n\"{txt}\"")
            context_str = "\n\n".join(context_items)

        history_str = ""
        if history:
            history_lines = [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history[-4:]]
            history_str = "CONVERSATION HISTORY:\n" + "\n".join(history_lines) + "\n\n"

        full_prompt = f"{history_str}STUDENT QUESTION: \"{user_query}\"\n\nRETRIEVED NOTEBOOK MEMORIES (IF RELEVANT):\n{context_str if context_str else 'No prior notebook memories matched.'}\n\nPlease generate an intelligent, structured study tutor response."

        response_text = lyzr_framework.execute_agent_prompt(
            agent_name="Assistant",
            system_instructions=SYSTEM_INSTRUCTIONS,
            user_input=full_prompt,
            temperature=0.3
        )

        status = lyzr_framework.get_framework_status()

        if "Offline Engine Fallback" in response_text and relevant_memories:
            notes_bullets = "\n".join([
                f"- **[{m.get('subject', 'General')} - {m.get('topic', 'Topic')}]**: {m.get('text')}"
                for m in relevant_memories[:3]
            ])
            response_text += f"\n\n### Saved Study Notebook Entries:\n{notes_bullets}"

        return {
            "answer": response_text,
            "retrieved_memories_count": len(relevant_memories),
            "ai_provider": status,
            "sources": [
                {
                    "subject": m.get("subject"),
                    "topic": m.get("topic"),
                    "snippet": m.get("text", "")[:120] + "...",
                    "score": m.get("score", 1.0)
                }
                for m in relevant_memories
            ]
        }

study_assistant_agent = StudyAssistantAgent()
