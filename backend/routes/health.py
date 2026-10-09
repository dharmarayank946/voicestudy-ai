from fastapi import APIRouter
import os
from backend.memory.qdrant_service import memory_service
from backend.services.lyzr_agent_framework import lyzr_framework
from backend.services.voice_adapter import voice_adapter

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health")
def health_check():
    stats = memory_service.get_stats()
    voice_status = voice_adapter.get_adapter_status()
    lyzr_status = lyzr_framework.get_framework_status()
    
    llm_key = (os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
    
    return {
        "status": "healthy",
        "service": "VoiceStudy AI",
        "version": "1.0.0",
        "vector_memory": {
            "status": "connected",
            "provider": "Qdrant",
            "storage_mode": stats.get("storage_mode"),
            "storage_path": stats.get("storage_path"),
            "total_memories": stats.get("total_memories", 0),
            "vector_dimension": stats.get("vector_dimension", 1536)
        },
        "agents": {
            "orchestrator": "active",
            "study_memory_agent": "active",
            "study_assistant_agent": "active",
            "quiz_agent": "active",
            "lyzr_framework": lyzr_status["mode"],
            "lyzr_details": lyzr_status,
            "llm_provider": "openai_api" if (llm_key and llm_key.startswith("sk-")) else "offline_fallback"
        },
        "voice": voice_status
    }

