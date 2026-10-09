import os
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("voicestudy.voice")

class VoiceInputPayload(BaseModel):
    source: str = "web_speech"  # 'omi' or 'web_speech' or 'text_fallback'
    transcript: str
    audio_format: Optional[str] = None
    device_id: Optional[str] = "browser_mic"
    metadata: Optional[Dict[str, Any]] = None

class OmiVoiceAdapter:
    """
    Adapter interface for Omi Wearable / Voice API integration.
    Allows seamless ingestion of real-time audio transcriptions from Omi devices,
    webhooks, or browser speech API fallback.
    """
    def __init__(self):
        self.api_key = os.getenv("OMI_API_KEY", "")
        self.webhook_secret = os.getenv("OMI_WEBHOOK_SECRET", "")
        self.is_connected = bool(self.api_key)

    def process_incoming_voice(self, payload: VoiceInputPayload) -> Dict[str, Any]:
        """
        Process incoming transcript from Omi device or Web Speech API.
        Normalizes voice input into clean text for agent processing.
        """
        logger.info(f"Processing voice input from source: {payload.source} | Device: {payload.device_id}")
        
        # Clean & sanitize transcript
        transcript_clean = payload.transcript.strip()
        
        return {
            "source": payload.source,
            "transcript": transcript_clean,
            "device_id": payload.device_id,
            "omi_authenticated": self.is_connected if payload.source == "omi" else False,
            "word_count": len(transcript_clean.split())
        }

    def get_adapter_status(self) -> Dict[str, Any]:
        return {
            "omi_sdk_configured": bool(self.api_key),
            "webhook_ready": bool(self.webhook_secret),
            "fallback_active": True,
            "supported_sources": ["omi_wearable", "omi_webhook", "web_speech_api", "text_fallback"]
        }

voice_adapter = OmiVoiceAdapter()
