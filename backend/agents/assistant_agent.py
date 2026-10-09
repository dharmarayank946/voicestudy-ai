import logging
from typing import Dict, Any, List
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.assistant_agent")

SYSTEM_INSTRUCTIONS = """You are the Study Assistant Agent for VoiceStudy AI.
Your goal is to answer student questions and provide explanations using retrieved Qdrant study memories.

Rules:
1. Base your answer primarily on the provided RETRIEVED STUDY MEMORIES.
2. If retrieved memories exist, clearly reference what the student studied (e.g. "Based on your study notes from DBMS concurrency control...").
3. Format your output with markdown: use bold headers, clean bullet points, and key takeaways.
4. Keep explanations clear, engaging, and easy to review for quick revision.
5. If no memories exist or match, politely inform the student and offer a brief standard answer while suggesting they save a note on this topic.
"""

class StudyAssistantAgent:
    def __init__(self):
        self.name = "Study Assistant Agent"

    def answer_question(self, user_query: str, retrieved_memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a contextual study response grounded in retrieved Qdrant memories."""
        logger.info(f"Study Assistant generating answer for: '{user_query[:60]}'")

        context_str = ""
        if retrieved_memories:
            context_items = []
            for idx, m in enumerate(retrieved_memories, 1):
                sub = m.get("subject", "General")
                top = m.get("topic", "Topic")
                dt = m.get("date_display", "Recent")
                txt = m.get("text", "")
                context_items.append(f"Memory #{idx} [{sub} - {top} ({dt})]:\n\"{txt}\"")
            context_str = "\n\n".join(context_items)
        else:
            context_str = "No prior study memories matched this query in Qdrant vector storage."

        full_prompt = f"""Student Question: "{user_query}"

RETRIEVED STUDY MEMORIES FROM QDRANT:
{context_str}

Please generate a comprehensive, accurate study assistance response."""

        response_text = lyzr_framework.execute_agent_prompt(
            agent_name="Assistant",
            system_instructions=SYSTEM_INSTRUCTIONS,
            user_input=full_prompt,
            temperature=0.3
        )

        # If offline fallback returned generic message, augment with exact retrieved memory snippets
        if "Based on your study memories" in response_text and retrieved_memories:
            notes_bullets = "\n".join([
                f"• **[{m.get('subject', 'General')} - {m.get('topic', 'Topic')}]**: {m.get('text')}"
                for m in retrieved_memories[:3]
            ])
            response_text = f"### 📚 Retrieved Study Memories from Qdrant:\n\n{notes_bullets}\n\n### 💡 Key Revision Summary:\n- **Core Concepts**: You studied key database and system fundamentals related to your query.\n- **Active Recall Tip**: Review the mechanisms above to prepare for your revision quiz!"

        return {
            "answer": response_text,
            "retrieved_memories_count": len(retrieved_memories),
            "sources": [
                {
                    "subject": m.get("subject"),
                    "topic": m.get("topic"),
                    "snippet": m.get("text", "")[:120] + "...",
                    "score": m.get("score", 1.0)
                }
                for m in retrieved_memories
            ]
        }

study_assistant_agent = StudyAssistantAgent()
