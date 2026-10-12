# VoiceStudy AI — System Architecture & Workflow

> **AI House × HiDevs Hackathon — Meeting & Lecture Intelligence**  
> **Integrated Stack:** Omi Voice Hardware & Simulator × Qdrant Vector Memory × Lyzr AI Multi-Agent Studio

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Client & Ingestion Layer"]
        UserVoice["Student Spoken Voice / Microphone"]
        OmiDevice["Omi Wearable / Hardware"]
        OmiSim["Omi Webhook Simulator (UI)"]
        BrowserUI["VoiceStudy AI React Frontend (Vite)"]
    end

    subgraph BackendAPI ["2. FastAPI Backend Engine (Python 3.11 / Render)"]
        OmiEndpoints["Omi Webhooks:\nPOST /omi/conversation\nPOST /omi/realtime"]
        StudyEndpoint["Study & Chat API:\nPOST /api/study\nPOST /api/chat"]
        MemoryEndpoints["Memory Management API:\nGET /api/memory/recent\nPOST /api/memory/search\nDELETE /api/memory/{id}"]
        VoiceAdapter["Voice Adapter & Defensive Parser"]
        BackgroundTasks["Async Background Worker (<50ms webhook response)"]
    end

    subgraph MemoryLayer ["3. Vector Memory Layer (Qdrant)"]
        Embedder["Embedding Engine:\nOpenAI text-embedding-3-small (1536-dim)\n+ Deterministic Vector Fallback"]
        QdrantStore[("Qdrant Vector Database:\nCollection: study_memories\n- UID Tenant Isolation\n- Subject Category Filtering\n- Cosine Distance Metric")]
    end

    subgraph AgentLayer ["4. Lyzr Agent Studio V3 Framework"]
        LyzrAPI["Lyzr Studio V3 Chat API Engine\n(https://agent-prod.studio.lyzr.ai/v3/inference/chat/)"]
        ManagerAgent["Manager Agent (Coordinator)"]
        Orchestrator["Orchestrator Agent (Intent & Subject Classification)"]
        AssistantAgent["Study Assistant Agent (Grounded Tutor Q&A)"]
        QuizAgent["Quiz Agent (Active Recall 5-Question MCQ)"]
        SummarizerAgent["Summarizer Agent (Lecture Digest)"]
        ActionItemAgent["Action Item Extractor Agent"]
    end

    subgraph ResponseFlow ["5. Presentation & Audio Synthesis Layer"]
        UIResponse["Dynamic Glassmorphic Response UI"]
        MemoryCitations["Cited Study Notebook Entries"]
        TTS["Web Speech Audio Voice Synthesis"]
    end

    %% Flow connections
    OmiDevice -->|"Webhook POST"| OmiEndpoints
    OmiSim -->|"Simulated Transcript"| OmiEndpoints
    UserVoice -->|"Speech-to-Text"| BrowserUI
    BrowserUI -->|"REST API Calls"| StudyEndpoint
    BrowserUI -->|"Search & History"| MemoryEndpoints

    OmiEndpoints --> VoiceAdapter
    VoiceAdapter --> BackgroundTasks
    BackgroundTasks --> Embedder
    StudyEndpoint --> Orchestrator
    MemoryEndpoints --> Embedder

    Embedder -->|"1536-dim Vectors"| QdrantStore
    Orchestrator --> ManagerAgent
    ManagerAgent -->|"Query Vector Search (UID + Subject Filter)"| QdrantStore
    QdrantStore -->|"Relevant Memory Snippets"| ManagerAgent

    ManagerAgent --> LyzrAPI
    LyzrAPI --> AssistantAgent
    LyzrAPI --> QuizAgent
    LyzrAPI --> SummarizerAgent
    LyzrAPI --> ActionItemAgent

    AssistantAgent --> UIResponse
    QuizAgent --> UIResponse
    SummarizerAgent --> UIResponse
    ActionItemAgent --> UIResponse
    QdrantStore -.->|"Grounding Sources"| MemoryCitations
    UIResponse --> TTS
```

---

## 2. End-to-End Workflow Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student / Learner
    participant UI as VoiceStudy UI (React)
    participant API as FastAPI Backend (Render)
    participant Qdrant as Qdrant Vector Store
    participant Lyzr as Lyzr Studio V3 Agent

    Note over Student,API: Step 1: Lecture Capture & Memory Ingestion
    Student->>UI: Speaks notes or submits Omi transcript simulator
    UI->>API: POST /omi/conversation?uid={uid}
    API-->>UI: HTTP 200 (Instant acknowledgement <50ms)
    Note right of API: Async Background Task: Parse & Embed
    API->>Qdrant: Store 1536-dim vector with payload (uid, subject, topic, text)

    Note over Student,Lyzr: Step 2: Intelligent Study & Retrieval
    Student->>UI: Asks study question (e.g., "Explain TCP vs UDP" or "What is photosynthesis?")
    UI->>API: POST /api/study {transcript, uid, subject_override}
    API->>API: Orchestrator analyzes intent & subject
    API->>Qdrant: Semantic search (vector similarity + UID isolation + subject filter)
    Qdrant-->>API: Returns relevant memories (or empty if general question)
    API->>Lyzr: POST /v3/inference/chat/ {agent_id, session_id, message: prompt + context}
    Lyzr-->>API: Synthesizes intelligent tutor response
    API-->>UI: HTTP 200 {message, retrieved_memories, intent, provider}
    UI->>Student: Displays structured answer, notebook citations, and speaks audio
```

---

## 3. Technology Integration Verification

| Component | Integrated Technology | Implementation File | Verification Status |
| :--- | :--- | :--- | :--- |
| **Voice Input** | Omi Wearable Webhook API | [`backend/routes/omi.py`](file:///d:/Projects/VOICESTUDY%20AI/backend/routes/omi.py), [`backend/services/omi_parser.py`](file:///d:/Projects/VOICESTUDY%20AI/backend/services/omi_parser.py) | **Verified** (Fast HTTP 200, non-blocking background persistence) |
| **Vector Memory** | Qdrant Vector Database | [`backend/memory/qdrant_service.py`](file:///d:/Projects/VOICESTUDY%20AI/backend/memory/qdrant_service.py) | **Verified** (1536-dim embeddings, UID isolation, keyword + subject filters) |
| **AI Agents** | Lyzr Studio V3 Agents | [`backend/services/lyzr_agent_framework.py`](file:///d:/Projects/VOICESTUDY%20AI/backend/services/lyzr_agent_framework.py), [`backend/agents/`](file:///d:/Projects/VOICESTUDY%20AI/backend/agents) | **Verified** (Live Lyzr V3 HTTP 200 calls, unique session isolation) |
| **Frontend UI** | React + Vite Single Page App | [`frontend/src/`](file:///d:/Projects/VOICESTUDY%20AI/frontend/src) | **Verified** (Glassmorphic dark UI, speech synthesis, subject filtering) |
