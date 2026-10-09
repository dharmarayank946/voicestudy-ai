import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("voicestudy.main")

# Initialize FastAPI App
app = FastAPI(
    title="VoiceStudy AI Backend",
    description="Voice-First AI Study Assistant powered by Lyzr Agents, Qdrant Vector Memory, and Omi Voice Adapter",
    version="1.0.0"
)

# Enable CORS for React frontend (GitHub Pages & local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dharmarayank946.github.io",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import routes
from backend.routes.health import router as health_router
from backend.routes.study import router as study_router
from backend.routes.memory import router as memory_router
from backend.routes.quiz import router as quiz_router
from backend.routes.omi import router as omi_router

app.include_router(health_router)
app.include_router(study_router)
app.include_router(memory_router)
app.include_router(quiz_router)
app.include_router(omi_router)

@app.on_event("startup")
def startup_populate_sample_memories():
    """Populate sample study memories into Qdrant if collection is empty."""
    from backend.memory.qdrant_service import memory_service
    try:
        stats = memory_service.get_stats()
        if stats["total_memories"] == 0:
            logger.info("Populating initial sample study memories into Qdrant vector store...")
            
            sample_notes = [
                {
                    "text": "Studied DBMS Concurrency Control today. Learned about Two-Phase Locking (2PL), Strict 2PL, and Timestamp Ordering protocols to prevent dirty reads and unrepeatable reads.",
                    "subject": "DBMS",
                    "topic": "Concurrency Control",
                    "memory_type": "voice_note"
                },
                {
                    "text": "Reviewed Computer Networks TCP vs UDP. TCP is connection-oriented with 3-way handshake, congestion control, and byte stream reliability. UDP is connectionless, fast, header size 8 bytes.",
                    "subject": "Computer Networks",
                    "topic": "TCP and UDP Protocols",
                    "memory_type": "voice_note"
                },
                {
                    "text": "Operating Systems Page Replacement Algorithms. Studied LRU (Least Recently Used), FIFO, and Optimal Page Replacement algorithm. LRU uses stack or reference bits.",
                    "subject": "Operating Systems",
                    "topic": "Virtual Memory & Paging",
                    "memory_type": "lecture_summary"
                }
            ]
            for note in sample_notes:
                memory_service.save_memory(
                    text=note["text"],
                    subject=note["subject"],
                    topic=note["topic"],
                    memory_type=note["memory_type"]
                )
            logger.info("Initial study memories successfully loaded into Qdrant.")
    except Exception as e:
        logger.warning(f"Error seeding initial study memories: {e}")

@app.get("/")
def root():
    return {
        "message": "Welcome to VoiceStudy AI Backend API",
        "tagline": "Speak. Remember. Revise.",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
