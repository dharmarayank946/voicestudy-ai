import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from backend.services.voice_adapter import voice_adapter, VoiceInputPayload
from backend.agents.orchestrator import orchestrator_agent
from backend.agents.memory_agent import study_memory_agent
from backend.agents.assistant_agent import study_assistant_agent
from backend.agents.quiz_agent import quiz_agent

logger = logging.getLogger("voicestudy.study")

router = APIRouter(prefix="/api", tags=["Study"])

class StudyRequest(BaseModel):
    transcript: str
    source: Optional[str] = "web_speech"  # 'omi', 'web_speech', 'text_fallback'
    device_id: Optional[str] = "browser_mic"
    uid: Optional[str] = None
    subject_override: Optional[str] = None
    topic_override: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/study")
@router.post("/chat")
def process_study_request(req: StudyRequest):
    if not req.transcript or not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Voice or text input transcript cannot be empty.")

    user_uid = req.uid or (req.metadata.get("uid") if req.metadata else None)

    # 1. Voice Adapter processing
    voice_payload = VoiceInputPayload(
        source=req.source or "web_speech",
        transcript=req.transcript.strip(),
        device_id=req.device_id or "browser_mic",
        metadata=req.metadata
    )
    processed_voice = voice_adapter.process_incoming_voice(voice_payload)
    clean_transcript = processed_voice["transcript"]

    # 2. Orchestrator Agent Intent Analysis
    intent_data = orchestrator_agent.analyze_intent(clean_transcript)
    intent = intent_data["intent"]
    subject = req.subject_override or intent_data["subject"]
    topic = req.topic_override or intent_data["topic"]

    # 3. Dispatch to specialized agent workflow based on intent
    response_dict = {}
    if intent == "REMEMBER":
        saved_result = study_memory_agent.save_study_memory(
            text=clean_transcript,
            subject=subject,
            topic=topic,
            memory_type="voice_note" if req.source in ["omi", "web_speech"] else "text_note",
            uid=user_uid
        )
        response_dict = {
            "intent": intent,
            "orchestration": intent_data,
            "voice_meta": processed_voice,
            "agent_executed": "Study Memory Agent",
            "message": f"Saved study note under '{subject} - {topic}' in Qdrant.",
            "response_type": "memory_saved",
            "retrieved_memories": [],
            "data": saved_result
        }

    elif intent in ["RETRIEVE", "EXPLAIN"]:
        retrieved_memories = study_memory_agent.retrieve_relevant_memories(
            query=clean_transcript,
            limit=4,
            uid_filter=user_uid
        )
        assistant_reply = study_assistant_agent.answer_question(
            user_query=clean_transcript,
            retrieved_memories=retrieved_memories
        )
        response_dict = {
            "intent": intent,
            "orchestration": intent_data,
            "voice_meta": processed_voice,
            "agent_executed": "Study Assistant Agent",
            "message": assistant_reply["answer"],
            "response_type": "answer",
            "retrieved_memories": retrieved_memories,
            "data": {
                "answer": assistant_reply["answer"],
                "sources": assistant_reply["sources"],
                "memories_count": len(retrieved_memories)
            }
        }

    elif intent == "QUIZ":
        retrieved_memories = study_memory_agent.retrieve_relevant_memories(
            query=clean_transcript,
            limit=5,
            uid_filter=user_uid
        )
        quiz_data = quiz_agent.generate_quiz(
            topic_or_subject=topic if topic != "General Study" else subject,
            num_questions=5,
            difficulty="medium",
            retrieved_memories=retrieved_memories
        )
        response_dict = {
            "intent": intent,
            "orchestration": intent_data,
            "voice_meta": processed_voice,
            "agent_executed": "Quiz Agent",
            "message": f"Generated {quiz_data.get('count', 5)} revision questions based on your study history.",
            "response_type": "quiz",
            "retrieved_memories": retrieved_memories,
            "data": quiz_data
        }

    elif intent == "SUMMARIZE":
        summary_data = study_memory_agent.summarize_study_history()
        retrieved_memories = study_memory_agent.retrieve_relevant_memories(query=clean_transcript, limit=5, uid_filter=user_uid)
        response_dict = {
            "intent": intent,
            "orchestration": intent_data,
            "voice_meta": processed_voice,
            "agent_executed": "Study Memory Agent",
            "message": summary_data["summary"],
            "response_type": "summary",
            "retrieved_memories": retrieved_memories,
            "data": summary_data
        }

    else:
        # Fallback default
        retrieved_memories = study_memory_agent.retrieve_relevant_memories(query=clean_transcript, limit=3, uid_filter=user_uid)
        assistant_reply = study_assistant_agent.answer_question(clean_transcript, retrieved_memories)
        response_dict = {
            "intent": "RETRIEVE",
            "orchestration": intent_data,
            "voice_meta": processed_voice,
            "agent_executed": "Study Assistant Agent",
            "message": assistant_reply["answer"],
            "response_type": "answer",
            "retrieved_memories": retrieved_memories,
            "data": assistant_reply
        }

    logger.info(f"[APP] Final response returned for intent={response_dict.get('intent')} | Agent: {response_dict.get('agent_executed')}")
    return response_dict

@router.post("/voice/omi-webhook")
def omi_webhook(payload: Dict[str, Any]):
    """
    Webhook endpoint to directly connect Omi Wearable transcription stream.
    Accepts Omi webhook payload and forwards to study pipeline.
    """
    transcript = payload.get("transcript") or payload.get("text") or payload.get("body", "")
    if not transcript:
        return {"status": "ignored", "reason": "empty_transcript"}

    study_req = StudyRequest(
        transcript=transcript,
        source="omi",
        device_id=payload.get("device_id", "omi_wearable_01"),
        metadata=payload
    )
    return process_study_request(study_req)
