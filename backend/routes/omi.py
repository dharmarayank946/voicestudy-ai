import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Request, Query, HTTPException
from backend.services.omi_parser import parse_omi_conversation_payload, parse_omi_realtime_payload
from backend.memory.qdrant_service import memory_service
from backend.agents.orchestrator import orchestrator_agent

logger = logging.getLogger("voicestudy.omi_webhook")

router = APIRouter(tags=["Omi Webhooks"])

# In-memory circular log buffer for development JSON inspection
MAX_LOG_ENTRIES = 50
OMI_WEBHOOK_LOGS: List[Dict[str, Any]] = []

def sanitize_payload(obj: Any) -> Any:
    """Sanitize payload dictionary to mask sensitive secrets."""
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            if any(secret_kw in k.lower() for secret_kw in ["api_key", "secret", "token", "password", "authorization", "key"]):
                sanitized[k] = "***MASKED***"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    elif isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    return obj

def add_omi_log(event_type: str, raw_payload: Dict[str, Any], uid: str):
    """Record sanitized webhook entry for dev inspection."""
    logger.info(f"[OMI] Transcript received for uid={uid} | Event: {event_type}")
    log_entry = {
        "id": len(OMI_WEBHOOK_LOGS) + 1,
        "event_type": event_type,
        "uid": uid,
        "received_at": datetime.utcnow().isoformat(),
        "sanitized_payload": sanitize_payload(raw_payload)
    }
    OMI_WEBHOOK_LOGS.insert(0, log_entry)
    if len(OMI_WEBHOOK_LOGS) > MAX_LOG_ENTRIES:
        OMI_WEBHOOK_LOGS.pop()

def process_omi_conversation_background(payload: Dict[str, Any], uid: str):
    """
    Background worker task to parse Omi conversation, classify intent/subject,
    and persist into Qdrant vector memory associated with Omi UID.
    """
    try:
        parsed = parse_omi_conversation_payload(payload, uid_query=uid)
        content = parsed.get("content", "").strip()

        if not content:
            logger.warning(f"[Omi Background] Empty content extracted for uid={uid}")
            return

        # Intent & metadata classification via Orchestrator Agent
        intent_data = orchestrator_agent.analyze_intent(content)
        subject = parsed.get("category") or intent_data.get("subject", "General")
        topic = parsed.get("title") or intent_data.get("topic", "Omi Voice Session")

        # Save to Qdrant persistent memory with UID association
        memory_record = memory_service.save_memory(
            text=content,
            subject=subject if subject != "General Study" else intent_data.get("subject", "General"),
            topic=topic if topic != "Omi Voice Session" else intent_data.get("topic", "Study Memory"),
            memory_type="omi_conversation",
            uid=parsed["uid"],
            metadata={
                "source": "omi_conversation",
                "omi_uid": parsed["uid"],
                "session_id": parsed.get("session_id"),
                "structured_overview": parsed.get("overview"),
                "speaker": parsed.get("speaker"),
                "raw_segments_count": parsed.get("raw_segments_count", 0),
                "intent_detected": intent_data.get("intent")
            }
        )
        logger.info(f"[Omi Background] Successfully persisted conversation memory for uid={parsed['uid']} | Memory ID: {memory_record.get('id')}")

    except Exception as e:
        logger.error(f"[Omi Background] Failed to process conversation webhook for uid={uid}: {e}", exc_info=True)


def process_omi_realtime_background(payload: Dict[str, Any], uid: str):
    """
    Background worker task for Omi real-time transcript segments.
    """
    try:
        parsed = parse_omi_realtime_payload(payload, uid_query=uid)
        text = parsed.get("text", "").strip()

        if not text:
            return

        memory_service.save_memory(
            text=text,
            subject="Omi Realtime Segment",
            topic="Live Voice Note",
            memory_type="omi_realtime",
            uid=parsed["uid"],
            metadata={
                "source": "omi_realtime",
                "omi_uid": parsed["uid"],
                "speaker": parsed.get("speaker"),
                "session_id": parsed.get("session_id")
            }
        )
        logger.info(f"[Omi Background] Persisted real-time transcript segment for uid={parsed['uid']}")

    except Exception as e:
        logger.error(f"[Omi Background] Failed to process real-time segment for uid={uid}: {e}", exc_info=True)


# ==========================================
# OMI WEBHOOK ENDPOINTS (Top Level & /api)
# ==========================================

@router.post("/omi/conversation")
@router.post("/api/omi/conversation")
async def omi_conversation_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    uid: Optional[str] = Query(None)
):
    """
    Official Omi Completed Conversation Webhook.
    Extracts user UID, logs sanitized request, queues Qdrant memory storage,
    and returns HTTP 200 immediately.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    actual_uid = uid or request.query_params.get("uid") or payload.get("uid") or "default_omi_user"

    add_omi_log("conversation", payload, str(actual_uid))
    background_tasks.add_task(process_omi_conversation_background, payload, str(actual_uid))

    return {
        "status": "success",
        "message": "Omi conversation webhook received and queued for processing",
        "uid": str(actual_uid),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/omi/realtime")
@router.post("/api/omi/realtime")
async def omi_realtime_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    uid: Optional[str] = Query(None)
):
    """
    Official Omi Real-time Transcript Segment Webhook.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    actual_uid = uid or request.query_params.get("uid") or payload.get("uid") or "default_omi_user"

    add_omi_log("realtime", payload, str(actual_uid))
    background_tasks.add_task(process_omi_realtime_background, payload, str(actual_uid))

    return {
        "status": "success",
        "message": "Omi realtime webhook segment received",
        "uid": str(actual_uid),
        "timestamp": datetime.utcnow().isoformat()
    }


# ==========================================
# DEV INSPECTION & TEST ENDPOINTS
# ==========================================

@router.get("/omi/logs")
@router.get("/api/omi/logs")
def get_omi_webhook_logs(limit: int = Query(default=20, le=50)):
    """Inspect recent sanitized Omi webhook logs received by FastAPI."""
    return {
        "total_logged": len(OMI_WEBHOOK_LOGS),
        "logs": OMI_WEBHOOK_LOGS[:limit]
    }


@router.get("/omi/latest")
@router.get("/api/omi/latest")
def get_latest_omi_payload():
    """Retrieve the single most recent raw Omi webhook payload received."""
    if not OMI_WEBHOOK_LOGS:
        return {"status": "empty", "message": "No Omi webhook payloads received yet."}
    return OMI_WEBHOOK_LOGS[0]


@router.delete("/omi/logs")
@router.delete("/api/omi/logs")
def clear_omi_logs():
    """Clear developer Omi log buffer."""
    global OMI_WEBHOOK_LOGS
    OMI_WEBHOOK_LOGS = []
    return {"status": "cleared", "message": "Omi log buffer cleared"}


@router.post("/omi/test")
@router.post("/api/omi/test")
def simulate_omi_webhook_test(
    background_tasks: BackgroundTasks,
    uid: str = Query(default="test_omi_user_99")
):
    """
    Dev tool: Post a realistic sample Omi conversation payload to test the full pipeline.
    """
    sample_payload = {
        "uid": uid,
        "session_id": "test_session_101",
        "structured": {
            "title": "DBMS Concurrency Control Revision",
            "overview": "Reviewed Two-Phase Locking (2PL), Strict 2PL, and Timestamp Ordering protocols to prevent dirty reads and unrepeatable reads.",
            "category": "DBMS",
            "action_items": ["Review Strict 2PL proof", "Practice lock conversion exercises"]
        },
        "transcript_segments": [
            {
                "text": "Today I spent time reviewing DBMS Concurrency Control and transaction management protocols.",
                "speaker": "SPEAKER_00",
                "is_user": True,
                "start": 0.0,
                "end": 4.5
            },
            {
                "text": "Two phase locking ensures serializability by having a growing phase where locks are acquired and a shrinking phase where locks are released.",
                "speaker": "SPEAKER_00",
                "is_user": True,
                "start": 5.0,
                "end": 12.0
            }
        ]
    }

    add_omi_log("test_conversation", sample_payload, uid)
    background_tasks.add_task(process_omi_conversation_background, sample_payload, uid)

    return {
        "status": "success",
        "message": "Simulated Omi conversation webhook triggered",
        "uid": uid,
        "sample_payload": sample_payload
    }
