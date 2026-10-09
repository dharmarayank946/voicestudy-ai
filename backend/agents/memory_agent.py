import logging
from typing import Dict, Any, List, Optional
from backend.memory.qdrant_service import memory_service
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.memory_agent")

class StudyMemoryAgent:
    """
    Study Memory Agent for VoiceStudy AI.
    Handles semantic storage into Qdrant and retrieval of relevant student notes.
    """
    def __init__(self):
        self.name = "Study Memory Agent"

    def save_study_memory(
        self,
        text: str,
        subject: str = "General",
        topic: str = "Study Topic",
        memory_type: str = "voice_note",
        uid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save student notes into Qdrant vector memory."""
        logger.info(f"Memory Agent saving study note for {subject} - {topic} [uid={uid}]")
        saved_record = memory_service.save_memory(
            text=text,
            subject=subject,
            topic=topic,
            memory_type=memory_type,
            uid=uid
        )
        return {
            "status": "success",
            "message": f"Successfully stored study memory under '{subject}: {topic}' in persistent Qdrant memory.",
            "memory": saved_record
        }

    def retrieve_relevant_memories(
        self,
        query: str,
        limit: int = 4,
        subject_filter: Optional[str] = None,
        uid_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search against Qdrant vector store."""
        logger.info(f"Memory Agent searching Qdrant for query: '{query}' [uid_filter={uid_filter}]")
        memories = memory_service.search_memories(
            query=query,
            limit=limit,
            subject_filter=subject_filter,
            uid_filter=uid_filter
        )
        return memories

    def summarize_study_history(self) -> Dict[str, Any]:
        """Summarize stored study history."""
        memories = memory_service.get_all_memories(limit=20)
        stats = memory_service.get_stats()
        
        if not memories:
            return {
                "summary": "You haven't saved any study memories yet. Speak or type what you studied to get started!",
                "recent_topics": [],
                "total_memories": 0
            }

        topics_str = ", ".join(stats["topics_list"])
        system_instructions = "You are the Study Memory Agent. Summarize the student's study timeline and topics concisely in a friendly tone."
        user_prompt = f"Total memories: {stats['total_memories']}. Topics covered: {topics_str}. Here are the recent notes:\n" + "\n".join([f"- [{m.get('subject')}] {m.get('topic')}: {m.get('text')}" for m in memories[:8]])
        
        summary_text = lyzr_framework.execute_agent_prompt(
            agent_name="Memory",
            system_instructions=system_instructions,
            user_input=user_prompt
        )

        return {
            "summary": summary_text,
            "recent_topics": stats["topics_list"],
            "total_memories": stats["total_memories"],
            "stats": stats
        }

study_memory_agent = StudyMemoryAgent()
