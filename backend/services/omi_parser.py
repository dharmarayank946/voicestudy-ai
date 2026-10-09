import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("voicestudy.omi_parser")

def parse_omi_conversation_payload(payload: Dict[str, Any], uid_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Defensive parser for Omi conversation webhook payloads.
    Supports multiple versions of Omi payload structures including:
    - transcript_segments / segments
    - structured (title, overview, summary, action_items, category)
    - overview / text / transcript
    - speaker / is_user / start / end
    """
    if not isinstance(payload, dict):
        payload = {}

    # 1. Extract UID safely from query parameter, body, or fallback
    raw_uid = uid_query or payload.get("uid") or payload.get("user_id") or payload.get("session_id")
    uid = str(raw_uid).strip() if raw_uid else "default_omi_user"

    # 2. Extract Transcript Segments
    segments = payload.get("transcript_segments") or payload.get("segments") or []
    extracted_lines = []

    if isinstance(segments, list):
        for seg in segments:
            if isinstance(seg, dict):
                text = str(seg.get("text", "")).strip()
                if text:
                    speaker = seg.get("speaker")
                    if not speaker:
                        is_user = seg.get("is_user")
                        if is_user is True:
                            speaker = "User"
                        elif is_user is False:
                            speaker = "Assistant"
                        else:
                            speaker = "Speaker"
                    extracted_lines.append(f"{speaker}: {text}")
            elif isinstance(seg, str) and seg.strip():
                extracted_lines.append(seg.strip())

    full_transcript = "\n".join(extracted_lines) if extracted_lines else str(payload.get("text") or payload.get("transcript") or "").strip()

    # 3. Extract Structured Overview
    structured = payload.get("structured")
    overview_text = ""
    title = ""
    category = "General Study"
    action_items = []

    if isinstance(structured, dict):
        title = str(structured.get("title", "")).strip()
        overview_text = str(structured.get("overview") or structured.get("summary") or "").strip()
        category = str(structured.get("category", "General Study")).strip()
        action_items = structured.get("action_items", [])
    elif isinstance(structured, str):
        overview_text = structured.strip()

    if not overview_text and payload.get("overview"):
        ov = payload.get("overview")
        if isinstance(ov, str):
            overview_text = ov.strip()
        elif isinstance(ov, dict):
            overview_text = str(ov.get("text") or ov.get("summary") or "").strip()

    # 4. Combine Useful Content for Qdrant Storage
    content_parts = []
    if title:
        content_parts.append(f"Title: {title}")
    if overview_text:
        content_parts.append(f"Overview: {overview_text}")
    if action_items and isinstance(action_items, list):
        items_str = ", ".join([str(item) for item in action_items if item])
        if items_str:
            content_parts.append(f"Action Items: {items_str}")
    if full_transcript:
        content_parts.append(f"Transcript:\n{full_transcript}")

    combined_content = "\n\n".join(content_parts) if content_parts else str(payload.get("raw") or "Empty Omi Payload").strip()

    # 5. Session & Speaker Metadata
    session_id = payload.get("session_id") or payload.get("id") or payload.get("conversation_id")
    speaker = payload.get("speaker") or ("User" if payload.get("is_user") else "Omi User")

    return {
        "uid": uid,
        "content": combined_content,
        "transcript": full_transcript,
        "overview": overview_text,
        "title": title or "Omi Voice Session",
        "category": category or "General Study",
        "action_items": action_items if isinstance(action_items, list) else [],
        "session_id": str(session_id) if session_id else None,
        "speaker": str(speaker),
        "raw_segments_count": len(segments) if isinstance(segments, list) else 0,
        "source": "omi_conversation"
    }


def parse_omi_realtime_payload(payload: Dict[str, Any], uid_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Defensive parser for Omi real-time segment webhook payloads.
    """
    if not isinstance(payload, dict):
        payload = {}

    raw_uid = uid_query or payload.get("uid") or payload.get("user_id") or payload.get("session_id")
    uid = str(raw_uid).strip() if raw_uid else "default_omi_user"

    text = str(payload.get("text") or payload.get("transcript") or "").strip()

    if not text:
        segments = payload.get("segments") or payload.get("transcript_segments") or []
        if isinstance(segments, list):
            lines = []
            for seg in segments:
                if isinstance(seg, dict) and seg.get("text"):
                    lines.append(str(seg.get("text")).strip())
                elif isinstance(seg, str) and seg.strip():
                    lines.append(seg.strip())
            text = " ".join(lines)

    speaker = payload.get("speaker") or ("User" if payload.get("is_user") else "Speaker")
    session_id = payload.get("session_id") or payload.get("id")

    return {
        "uid": uid,
        "text": text.strip(),
        "speaker": str(speaker),
        "session_id": str(session_id) if session_id else None,
        "source": "omi_realtime"
    }
