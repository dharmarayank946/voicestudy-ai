import json
import logging
from typing import Dict, Any, List, Optional
from backend.services.lyzr_agent_framework import lyzr_framework, LyzrAPIError, LyzrTimeoutError
from backend.agents.summarizer_agent import summarizer_agent
from backend.agents.action_item_agent import action_item_agent
from backend.agents.assistant_agent import memory_assistant_agent
from backend.agents.memory_agent import study_memory_agent
from backend.agents.quiz_agent import quiz_agent

logger = logging.getLogger("voicestudy.manager_agent")

MANAGER_SYSTEM_PROMPT = """You are the Manager Agent for VoiceStudy AI (Meeting & Lecture Intelligence).
Your job is to analyze incoming user transcripts or requests, determine the optimal delegation plan, and decide whether a single specialized agent or multi-agent coordination is required.

The available specialized agents are:
1. "summarizer": Summarizes meeting and lecture transcripts into key points.
2. "action_items": Extracts tasks, owners, deadlines, and decisions without hallucination.
3. "memory_assistant": Answers user questions about past meetings, lectures, and concepts using Qdrant memories.
4. "quiz": Generates revision quiz questions on study topics.
5. "remember": Saves new notes or transcripts into persistent vector memory.

Analyze the prompt and respond strictly in JSON format:
{
  "routing": "SINGLE" or "MULTI",
  "delegation": ["summarizer"] or ["action_items"] or ["memory_assistant"] or ["quiz"] or ["remember"] or ["summarizer", "action_items"],
  "primary_intent": "SUMMARY" | "ACTION_ITEMS" | "QUESTION" | "QUIZ" | "REMEMBER" | "MULTI_AGENT",
  "subject": "Extracted Subject (e.g. Operating Systems, DBMS, Software Engineering, Team Standup, General)",
  "topic": "Specific Topic",
  "reasoning": "Reason for delegation"
}
"""

from backend.agents.orchestrator import orchestrator_agent

class ManagerAgent:
    def __init__(self):
        self.name = "Manager Agent"

    def plan_delegation(self, user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Classifies the user query into single or multi-agent delegation with subject/topic extraction."""
        logger.info(f"Manager Agent evaluating prompt: '{user_input[:80]}'")

        # 1. Base intent and subject/topic from orchestrator
        base_orch = orchestrator_agent.analyze_intent(user_input, history=history)
        subject = base_orch.get("subject", "General Study")
        topic = base_orch.get("topic", "General Concept")

        lower = user_input.lower()
        has_action_intent = any(k in lower for k in [
            "action item", "action items", "extract tasks", "list tasks", "tasks and owners",
            "deadlines", "assignment", "who is doing", "assigned to", "decisions made", "todo"
        ])
        has_summary_intent = any(k in lower for k in [
            "summarize", "summary", "overview", "recap", "key points", "main points"
        ])
        is_study_history_summary = any(k in lower for k in ["what i studied", "studied recently", "study history", "past notes", "my progress"])

        # 2. Check for multi-agent coordination (e.g. summarize AND action items)
        if has_action_intent and has_summary_intent:
            return {
                "routing": "MULTI",
                "delegation": ["summarizer", "action_items"],
                "primary_intent": "MULTI_AGENT",
                "subject": subject if subject != "General Study" else "Meeting & Lecture Intelligence",
                "topic": topic if topic != "General Concept" else "Summary & Action Items",
                "reasoning": "User requested multi-agent coordination (Summarizer + Action Items)."
            }

        # 3. Action items extraction
        if has_action_intent:
            return {
                "routing": "SINGLE",
                "delegation": ["action_items"],
                "primary_intent": "ACTION_ITEMS",
                "subject": subject if subject != "General Study" else "Meeting & Lecture Intelligence",
                "topic": topic if topic != "General Concept" else "Action Items",
                "reasoning": "User requested Action Item Extractor Agent."
            }

        # 4. Summarize: distinguish between study history timeline vs transcript summary
        if has_summary_intent:
            target_agent = "study_memory" if is_study_history_summary else "summarizer"
            return {
                "routing": "SINGLE",
                "delegation": [target_agent],
                "primary_intent": "SUMMARIZE",
                "subject": subject,
                "topic": topic,
                "reasoning": f"User requested summary via {target_agent}."
            }

        # 5. Respect other base intents from orchestrator (REMEMBER, QUIZ, EXPLAIN/RETRIEVE)
        base_intent = base_orch.get("intent", "EXPLAIN")
        if base_intent == "REMEMBER":
            return {
                "routing": "SINGLE",
                "delegation": ["remember"],
                "primary_intent": "REMEMBER",
                "subject": subject,
                "topic": topic,
                "reasoning": "User requested saving note into persistent Qdrant memory."
            }

        if base_intent == "QUIZ":
            return {
                "routing": "SINGLE",
                "delegation": ["quiz"],
                "primary_intent": "QUIZ",
                "subject": subject,
                "topic": topic,
                "reasoning": "User requested revision quiz."
            }

        return {
            "routing": "SINGLE",
            "delegation": ["memory_assistant"],
            "primary_intent": base_intent,
            "subject": subject,
            "topic": topic,
            "reasoning": "Knowledge question routed to Memory Assistant Agent."
        }

    def execute_request(
        self,
        transcript: str,
        user_uid: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        subject_override: Optional[str] = None,
        topic_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Coordinates single or multi-agent execution."""
        plan = self.plan_delegation(transcript, history=history)
        delegation = plan["delegation"]
        subject = subject_override or plan.get("subject", "General")
        topic = topic_override or plan.get("topic", "General")

        provider_status = lyzr_framework.get_framework_status()

        # Multi-Agent Coordination
        if len(delegation) > 1 or plan["routing"] == "MULTI":
            logger.info(f"Manager Agent coordinating multi-agent execution: {delegation}")
            executed_agents = []
            combined_sections = []
            retrieved_memories = []

            # 1. Summarizer Agent if requested
            if "summarizer" in delegation:
                sum_res = summarizer_agent.summarize_transcript(transcript)
                executed_agents.append(summarizer_agent.name)
                combined_sections.append(f"### Meeting & Lecture Summary\n{sum_res['summary']}")

            # 2. Action Item Extractor Agent if requested
            if "action_items" in delegation:
                act_res = action_item_agent.extract_action_items(transcript)
                executed_agents.append(action_item_agent.name)
                combined_sections.append(f"### Extracted Action Items & Decisions\n{act_res['action_items']}")

            # 3. Memory Assistant if requested
            if "memory_assistant" in delegation:
                retrieved_memories = study_memory_agent.retrieve_relevant_memories(
                    query=transcript,
                    limit=3,
                    uid_filter=user_uid
                )
                mem_res = memory_assistant_agent.answer_question(
                    user_query=transcript,
                    retrieved_memories=retrieved_memories,
                    history=history
                )
                executed_agents.append(memory_assistant_agent.name)
                combined_sections.append(f"### Historical Notes & Context (from Qdrant)\n{mem_res['answer']}")

            combined_message = "\n\n---\n\n".join(combined_sections)
            agent_label = f"Manager Agent ({' + '.join(executed_agents)})"

            return {
                "intent": "MULTI_AGENT",
                "orchestration": plan,
                "ai_provider": provider_status,
                "agent_executed": agent_label,
                "message": combined_message,
                "response_type": "multi_agent_summary",
                "retrieved_memories": retrieved_memories,
                "data": {
                    "agents_coordinated": executed_agents,
                    "sections_count": len(combined_sections)
                }
            }

        # Single Agent Delegation
        target = delegation[0] if delegation else "memory_assistant"

        if target == "summarizer":
            sum_res = summarizer_agent.summarize_transcript(transcript)
            return {
                "intent": "SUMMARIZE",
                "orchestration": plan,
                "ai_provider": provider_status,
                "agent_executed": "Summarizer Agent",
                "message": sum_res["summary"],
                "response_type": "summary",
                "retrieved_memories": [],
                "data": sum_res
            }

        elif target == "study_memory":
            hist_res = study_memory_agent.summarize_study_history()
            retrieved_memories = study_memory_agent.retrieve_relevant_memories(query=transcript, limit=5, uid_filter=user_uid)
            return {
                "intent": "SUMMARIZE",
                "orchestration": plan,
                "ai_provider": provider_status,
                "agent_executed": "Study Memory Agent",
                "message": hist_res["summary"],
                "response_type": "summary",
                "retrieved_memories": retrieved_memories,
                "data": hist_res
            }

        elif target == "action_items":
            act_res = action_item_agent.extract_action_items(transcript)
            return {
                "intent": "ACTION_ITEMS",
                "orchestration": plan,
                "ai_provider": provider_status,
                "agent_executed": "Action Item Extractor Agent",
                "message": act_res["action_items"],
                "response_type": "action_items",
                "retrieved_memories": [],
                "data": act_res
            }

        elif target == "quiz":
            retrieved_memories = study_memory_agent.retrieve_relevant_memories(
                query=transcript,
                limit=5,
                uid_filter=user_uid
            )
            quiz_data = quiz_agent.generate_quiz(
                topic_or_subject=topic if topic != "General" else subject,
                num_questions=5,
                difficulty="medium",
                retrieved_memories=retrieved_memories
            )
            return {
                "intent": "QUIZ",
                "orchestration": plan,
                "ai_provider": provider_status,
                "agent_executed": "Quiz Agent",
                "message": f"Generated {quiz_data.get('count', 5)} revision questions for {subject}.",
                "response_type": "quiz",
                "retrieved_memories": retrieved_memories,
                "data": quiz_data
            }

        elif target == "remember":
            saved_result = study_memory_agent.save_study_memory(
                text=transcript,
                subject=subject,
                topic=topic,
                memory_type="voice_note",
                uid=user_uid
            )
            return {
                "intent": "REMEMBER",
                "orchestration": plan,
                "ai_provider": provider_status,
                "agent_executed": "Study Memory Agent",
                "message": f"Saved study note under '{subject} - {topic}' in Qdrant.",
                "response_type": "memory_saved",
                "retrieved_memories": [],
                "data": saved_result
            }

        else: # memory_assistant
            retrieved_memories = study_memory_agent.retrieve_relevant_memories(
                query=transcript,
                limit=4,
                uid_filter=user_uid
            )
            assistant_reply = memory_assistant_agent.answer_question(
                user_query=transcript,
                retrieved_memories=retrieved_memories,
                history=history
            )
            return {
                "intent": "EXPLAIN",
                "orchestration": plan,
                "ai_provider": provider_status,
                "agent_executed": "Study Assistant Agent",
                "message": assistant_reply["answer"],
                "response_type": "answer",
                "retrieved_memories": retrieved_memories,
                "data": {
                    "answer": assistant_reply["answer"],
                    "sources": assistant_reply.get("sources", []),
                    "memories_count": len(retrieved_memories)
                }
            }

manager_agent = ManagerAgent()
