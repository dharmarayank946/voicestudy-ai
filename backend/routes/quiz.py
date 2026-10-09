from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.agents.quiz_agent import quiz_agent
from backend.agents.memory_agent import study_memory_agent

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

class GenerateQuizRequest(BaseModel):
    topic: Optional[str] = "Recent Studies"
    num_questions: Optional[int] = 5
    difficulty: Optional[str] = "medium"

@router.post("")
@router.post("/generate")
def generate_quiz(req: GenerateQuizRequest):
    topic = req.topic if req.topic and req.topic.strip() else "Recent Studies"
    
    try:
        raw_q = int(req.num_questions) if req.num_questions is not None else 5
    except (ValueError, TypeError):
        raw_q = 5

    if raw_q <= 3:
        num_q = 3
    elif raw_q >= 10:
        num_q = 10
    else:
        num_q = 5

    diff = req.difficulty if req.difficulty in ["easy", "medium", "hard"] else "medium"

    # Retrieve relevant study memories to build questions from
    retrieved = study_memory_agent.retrieve_relevant_memories(query=topic, limit=6)
    
    quiz_result = quiz_agent.generate_quiz(
        topic_or_subject=topic,
        num_questions=num_q,
        difficulty=diff,
        retrieved_memories=retrieved
    )
    return quiz_result
