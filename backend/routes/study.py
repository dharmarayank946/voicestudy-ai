import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from backend.services.voice_adapter import voice_adapter, VoiceInputPayload
from backend.agents.orchestrator import orchestrator_agent
from backend.agents.memory_agent import study_memory_agent
from backend.agents.assistant_agent import study_assistant_agent
from backend.agents.quiz_agent import quiz_agent
from backend.services.lyzr_agent_framework import lyzr_framework, LyzrAPIError, LyzrTimeoutError

from backend.agents.manager_agent import manager_agent

logger = logging.getLogger("voicestudy.study")

router = APIRouter(prefix="/api", tags=["Study"])

class StudyRequest(BaseModel):
    transcript: str
    source: Optional[str] = "web_speech"  # 'omi', 'web_speech', 'text_fallback'
    device_id: Optional[str] = "browser_mic"
    uid: Optional[str] = None
    subject_override: Optional[str] = None
    topic_override: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/study")
@router.post("/chat")
def process_study_request(req: StudyRequest):
    if not req.transcript or not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Voice or text input transcript cannot be empty.")

    user_uid = req.uid or (req.metadata.get("uid") if req.metadata else None)

    voice_payload = VoiceInputPayload(
        source=req.source or "web_speech",
        transcript=req.transcript.strip(),
        device_id=req.device_id or "browser_mic",
        metadata=req.metadata
    )
    processed_voice = voice_adapter.process_incoming_voice(voice_payload)
    clean_transcript = processed_voice["transcript"]

    try:
        response_dict = manager_agent.execute_request(
            transcript=clean_transcript,
            user_uid=user_uid,
            history=req.history,
            subject_override=req.subject_override,
            topic_override=req.topic_override
        )
        response_dict["voice_meta"] = processed_voice
    except (LyzrAPIError, LyzrTimeoutError) as err:
        logger.error(f"Lyzr Agent execution error: {err}")
        provider_status = lyzr_framework.get_framework_status()
        err_str = str(err)
        
        # User-friendly error diagnosis without leaking secrets
        if "401" in err_str or "403" in err_str or "Invalid API Key" in err_str:
            code_hint = " (HTTP 403 Forbidden)" if "403" in err_str else (" (HTTP 401 Unauthorized)" if "401" in err_str else "")
            friendly_detail = f"Lyzr API authentication failed{code_hint}: Invalid API key. Please verify your LYZR_API_KEY environment variable in server configuration."
            error_code = "LYZR_AUTH_ERROR"
        elif "timed out" in err_str.lower() or isinstance(err, LyzrTimeoutError):
            friendly_detail = "Lyzr API request timed out after 30 seconds. Please check your network connection and retry."
            error_code = "LYZR_TIMEOUT"
        elif "503" in err_str or "502" in err_str:
            friendly_detail = "Lyzr API returned HTTP 503: Service temporarily unavailable. Please retry shortly."
            error_code = "LYZR_SERVICE_UNAVAILABLE"
        else:
            friendly_detail = f"Lyzr API request failed: {err_str[:120]}"
            error_code = "LYZR_API_ERROR"

        response_dict = {
            "intent": "ERROR",
            "orchestration": {
                "subject": req.subject_override or "General",
                "topic": req.topic_override or "AI Agent Execution"
            },
            "voice_meta": processed_voice,
            "ai_provider": provider_status,
            "agent_executed": "Lyzr Agent",
            "message": f"Lyzr Agent Error: {friendly_detail}",
            "response_type": "error",
            "error_code": error_code,
            "retryable": True,
            "retrieved_memories": [],
            "data": {
                "error": friendly_detail,
                "error_code": error_code,
                "retryable": True,
                "memories_count": 0
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in study request execution: {e}")
        provider_status = lyzr_framework.get_framework_status()
        response_dict = {
            "intent": "ERROR",
            "orchestration": {"subject": "General", "topic": "General Execution"},
            "voice_meta": processed_voice,
            "ai_provider": provider_status,
            "agent_executed": "VoiceStudy Backend",
            "message": f"Internal execution error: {str(e)}",
            "response_type": "error",
            "retrieved_memories": [],
            "data": {"error": str(e)}
        }

    logger.info(f"[APP] Final response returned for intent={response_dict.get('intent')} | Agent: {response_dict.get('agent_executed')}")
    return response_dict

@router.post("/voice/omi-webhook")
def omi_webhook(payload: Dict[str, Any]):
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
