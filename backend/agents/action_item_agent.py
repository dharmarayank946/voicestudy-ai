import logging
from typing import Dict, Any, Optional
from backend.services.lyzr_agent_framework import lyzr_framework

logger = logging.getLogger("voicestudy.action_item_agent")

ACTION_ITEM_INSTRUCTIONS = """You are the Action Item Extractor Agent for VoiceStudy AI, specialized in Meeting & Lecture Intelligence.
Your task is to analyze conversational transcripts and extract action items, owners, deadlines, and key decisions.

CRITICAL RULES:
1. NEVER invent or hallucinate tasks, people, owners, dates, or deadlines not stated or clearly implied in the transcript.
2. If an owner is not mentioned for a task, label the owner as "Unassigned".
3. If a deadline or timeframe is not mentioned, label the deadline as "Not specified".
4. If there are no clear action items in the transcript, state clearly: "No explicit action items found in the provided transcript."

Structure your response using GitHub-flavored markdown:
### Action Items & Tasks
| # | Task | Owner | Deadline | Priority |
|---|---|---|---|---|
| 1 | [Task description] | [Name or Unassigned] | [Date/Time or Not specified] | [High / Medium / Normal] |

### Key Decisions Made
- [Decision 1]
- [Decision 2]
(Or "No formal decisions recorded" if none)

### Follow-ups & Open Questions
- [Any items requiring follow-up or unresolved questions]
"""

class ActionItemExtractorAgent:
    def __init__(self):
        self.name = "Action Item Extractor Agent"

    def extract_action_items(
        self,
        transcript: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"Action Item Extractor Agent analyzing transcript of {len(transcript)} chars")

        prompt_parts = []
        if context:
            prompt_parts.append(f"SESSION CONTEXT:\n{context}\n")
        prompt_parts.append(f"TRANSCRIPT TO EXTRACT ACTION ITEMS FROM:\n{transcript}\n\nPlease extract all action items, owners, deadlines, and decisions strictly following the instructions.")

        full_prompt = "\n".join(prompt_parts)

        response_text = lyzr_framework.execute_agent_prompt(
            agent_name="Action Items",
            system_instructions=ACTION_ITEM_INSTRUCTIONS,
            user_input=full_prompt,
            temperature=0.1
        )

        return {
            "action_items": response_text,
            "agent_executed": self.name,
            "length_processed": len(transcript)
        }

action_item_agent = ActionItemExtractorAgent()
