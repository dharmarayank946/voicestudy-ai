from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.agents.memory_agent import study_memory_agent
from backend.memory.qdrant_service import memory_service

router = APIRouter(prefix="/api/memory", tags=["Memory"])

class SaveMemoryRequest(BaseModel):
    text: str
    subject: Optional[str] = "General"
    topic: Optional[str] = "Study Topic"
    memory_type: Optional[str] = "voice_note"
    uid: Optional[str] = "default_omi_user"
    metadata: Optional[Dict[str, Any]] = None

class SearchMemoryRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    subject_filter: Optional[str] = None
    uid_filter: Optional[str] = None

@router.post("/save")
def save_memory(req: SaveMemoryRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Memory text content cannot be empty.")
    
    result = memory_service.save_memory(
        text=req.text.strip(),
        subject=req.subject or "General",
        topic=req.topic or "Study Topic",
        memory_type=req.memory_type or "voice_note",
        uid=req.uid or "default_omi_user",
        metadata=req.metadata
    )
    return result

@router.post("/search")
def search_memory(req: SearchMemoryRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
        
    memories = memory_service.search_memories(
        query=req.query.strip(),
        limit=req.limit or 5,
        subject_filter=req.subject_filter,
        uid_filter=req.uid_filter
    )
    return {
        "query": req.query,
        "count": len(memories),
        "results": memories
    }


@router.get("/recent")
def get_recent_memories(
    limit: int = Query(default=20, le=100),
    uid_filter: Optional[str] = Query(default=None)
):
    memories = memory_service.get_all_memories(limit=limit, uid_filter=uid_filter)
    stats = memory_service.get_stats()
    return {
        "total_count": stats["total_memories"],
        "subjects": stats["subjects_list"],
        "topics": stats["topics_list"],
        "memories": memories
    }


@router.delete("/{memory_id}")
def delete_memory(memory_id: str):
    success = memory_service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} could not be deleted.")
    return {"status": "success", "deleted_id": memory_id}

@router.get("/stats")
def get_memory_stats():
    return memory_service.get_stats()
