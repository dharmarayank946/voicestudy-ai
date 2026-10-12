import logging
from typing import Dict, Any, Optional
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.summarizer_agent")

SUMMARIZER_INSTRUCTIONS = """You are the Summarizer Agent for VoiceStudy AI, specialized in Meeting & Lecture Intelligence.
Your objective is to analyze meeting or lecture voice transcripts and generate a concise, high-value summary of key points.

Structure your response using clear markdown:
### Executive Summary
[A concise 2-3 sentence overview of the meeting or lecture]

### Key Points & Discussion Topics
- **[Topic 1]**: [Clear explanation of concepts or points discussed]
- **[Topic 2]**: [Clear explanation of concepts or points discussed]
- **[Topic 3]**: [Clear explanation of concepts or points discussed]

### Core Takeaways
- [Primary takeaway or conclusion]
- [Next steps or follow-ups mentioned]

Guidelines:
1. Stay faithful to the transcript content; do not extrapolate or invent facts.
2. Keep the formatting structured and readable for students and professionals.
"""

class SummarizerAgent:
    def __init__(self):
        self.name = "Summarizer Agent"

    def summarize_transcript(
        self,
        transcript: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"Summarizer Agent processing transcript of {len(transcript)} chars")

        prompt_parts = []
        if context:
            prompt_parts.append(f"SESSION CONTEXT:\n{context}\n")
        prompt_parts.append(f"TRANSCRIPT TO SUMMARIZE:\n{transcript}\n\nPlease generate a clear, structured summary of key points.")

        full_prompt = "\n".join(prompt_parts)

        response_text = lyzr_framework.execute_agent_prompt(
            agent_name="Summarizer",
            system_instructions=SUMMARIZER_INSTRUCTIONS,
            user_input=full_prompt,
            temperature=0.2
        )

        return {
            "summary": response_text,
            "agent_executed": self.name,
            "length_processed": len(transcript)
        }

summarizer_agent = SummarizerAgent()
