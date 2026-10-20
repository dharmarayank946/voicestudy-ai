import logging
from typing import Dict, Any, List, Optional
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.assistant_agent")

SYSTEM_INSTRUCTIONS = """You are the Study Assistant Agent for VoiceStudy AI, behaving like an intelligent AI tutor (ChatGPT-style).
Your goal is to provide clear, engaging, correct explanations for student questions across any educational subject (Science, Biology, Software Engineering, OS, DBMS, Networks, Mathematics, Programming, General).

Guidelines:
1. Explain concepts clearly using simple English, structured markdown, bold headers, bullet points, and practical examples.
2. If relevant study memories from the student's notebook are provided, cite and ground your answer on them, and clearly list them under a '### Saved Study Notebook Entries' section.
3. If no relevant study memories exist for the topic, DO NOT refuse to explain! Answer the student's question directly, thoroughly, and accurately from your knowledge as an expert educational tutor.
4. Clearly distinguish between personal memories recalled from the student's notebook and general subject explanations.
5. Never invent or claim that the student previously studied a topic in their notebook if no relevant memory was provided.
6. Keep answers helpful, concise, directly relevant, and structured for quick revision.
"""

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "and", "or",
    "what", "how", "why", "when", "where", "which", "who", "it", "its",
    "this", "that", "these", "those", "i", "you", "my", "your", "we", "can",
    "does", "do", "did", "tell", "explain", "me", "about", "studied", "learned", "note"
}

class StudyAssistantAgent:
    def __init__(self):
        self.name = "Study Assistant Agent"

    def answer_question(
        self,
        user_query: str,
        retrieved_memories: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None,
        subject_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"Study Assistant generating answer for: '{user_query[:60]}'")

        relevant_memories = []
        if retrieved_memories:
            import re
            q_keywords = set(re.findall(r'\b\w+\b', user_query.lower())) - STOP_WORDS
            for m in retrieved_memories:
                m_sub = (m.get("subject") or "").lower()
                m_top = (m.get("topic") or "").lower()
                m_txt = (m.get("text") or "").lower()
                m_score = float(m.get("score") or 0.0)
                
                m_words = set(re.findall(r'\b\w+\b', f"{m_txt} {m_sub} {m_top}".lower())) - STOP_WORDS
                overlap = len(q_keywords.intersection(m_words))
                is_sub_match = any(k in m_sub or k in m_top for k in q_keywords if len(k) > 2)
                
                # Check subject hint if provided
                hint_match = True
                if subject_hint and subject_hint.lower() not in ["all", "general", "general study"]:
                    hint_match = (subject_hint.lower() in m_sub or m_sub in subject_hint.lower())
                
                # A memory is relevant if keywords match and it is not a zero-similarity unrelated collision
                if hint_match and (overlap >= 2 or (overlap >= 1 and (is_sub_match or m_score >= 0.08)) or m_score >= 0.35):
                    relevant_memories.append(m)

        memories_to_use = relevant_memories
        if memories_to_use:
            context_items = []
            for idx, m in enumerate(memories_to_use, 1):
                sub = m.get("subject", "General")
                top = m.get("topic", "Topic")
                txt = m.get("text", "")
                context_items.append(f"Memory #{idx} [{sub} - {top}]:\n\"{txt}\"")
            context_str = "RETRIEVED NOTEBOOK MEMORIES (FROM QDRANT VECTOR STORE):\n" + "\n\n".join(context_items) + "\n\nInstruction: Ground your answer on these saved notes and cite them under '### Saved Study Notebook Entries'."
        else:
            context_str = "RETRIEVED NOTEBOOK MEMORIES (FROM QDRANT VECTOR STORE):\nNo relevant notebook memories matched this question in the student's personal saved notes.\n\nInstruction: Do NOT refuse to answer. Explain the concept thoroughly, clearly, and accurately from your knowledge as an educational AI tutor. Do NOT claim the student previously studied this topic in their notebook."

        history_str = ""
        if history:
            history_lines = [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history[-4:]]
            history_str = "CONVERSATION HISTORY (FOR FOLLOW-UP CONTEXT ONLY):\n" + "\n".join(history_lines) + "\n\n"

        full_prompt = f"{history_str}STUDENT QUESTION: \"{user_query}\"\n\n{context_str}\n\nPlease generate an intelligent, structured study tutor response."

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
            ],
            "relevant_memories": relevant_memories
        }

study_assistant_agent = StudyAssistantAgent()
MemoryAssistantAgent = StudyAssistantAgent
memory_assistant_agent = study_assistant_agent
