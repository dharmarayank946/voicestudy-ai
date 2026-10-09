# VoiceStudy AI — Official Hackathon Demo Script (5 Minutes)

> **Tagline:** Speak. Remember. Revise.  
> **Build Track:** Meeting & Lecture Intelligence  
> **Technologies:** Omi Wearable + Qdrant Vector DB + Lyzr Agent Framework  

---

## ⏱ Timeline & Walkthrough Script

### 0:00 – 0:30 | Problem & Introduction
- **Presenter Action:** Show VoiceStudy AI home screen with the glowing **Voice Orb**.
- **Script:**  
  *"Hi everyone! As students, we spend hours attending lectures and studying complex subjects, but we struggle with active recall and quick revision. Notes get scattered and forgotten.  
  Meet **VoiceStudy AI** — a voice-first AI study assistant that captures spoken study and lecture information via **Omi Wearable**, embeds it into **Qdrant Vector DB**, and uses **Lyzr Agents** for active recall and revision reasoning. Our build track is **Meeting & Lecture Intelligence**."*

---

### 0:30 – 1:30 | Live Voice Memory Capture via Omi
- **Presenter Action:** Speak naturally to Omi hardware (or trigger the Omi webhook simulator in the UI).
- **Voice Input:** *"I studied DBMS two phase locking and concurrency control protocols today."*
- **Visual Highlight:** Point to the **FastAPI Webhook Inspector** and the **Voice Orb** transitioning to `Remembering`.
- **Script:**  
  *"I just spoke a key study statement. Omi immediately sends the transcript and structured overview via FastAPI webhook (`POST /omi/conversation`).  
  Our backend generates a 1536-dimensional vector embedding and stores it permanently in Qdrant indexed by the student's unique Omi UID."*

---

### 1:30 – 2:30 | Qdrant Vector Memory Storage & Retrieval
- **Presenter Action:** Navigate to the **Memory View** tab.
- **Visual Highlight:** Show the newly stored Qdrant memory card tagged with `DBMS`, `Concurrency Control`, ISO timestamp, and `uid`. Click search to perform semantic vector retrieval.
- **Script:**  
  *"Here in our Memory Workspace, you can see the actual point in Qdrant. Notice how it captures the subject, topic, metadata, and UID.  
  If the student ever wants to remove a note, clicking 'Forget Memory' issues a real point deletion directly to Qdrant vector storage."*

---

### 2:30 – 3:30 | Question Answering & Lyzr Agent Reasoning
- **Presenter Action:** Return to **Study View** and speak or type:  
  *"What did I study about concurrency control?"*
- **Visual Highlight:** Show the live **Agent Workflow Pipeline** updating (`Qdrant Search` $\rightarrow$ `Memories Retrieved` $\rightarrow$ `Lyzr Agent Reasoning`).
- **Script:**  
  *"Now, when the student asks a revision question, FastAPI executes semantic vector search in Qdrant, retrieves top matching memories for that student's UID, and passes the retrieved context to the **Lyzr Assistant Agent**.  
  Lyzr synthesizes a comprehensive, grounded answer directly referencing our prior study note on Two-Phase Locking."*

---

### 3:30 – 4:20 | Active Recall Quiz & Study Timeline Summary
- **Presenter Action:** Click **Quiz View** or ask: *"Give me 5 revision questions from my recent study."*
- **Visual Highlight:** Display generated revision quiz cards with multiple choice options and answer keys.
- **Script:**  
  *"VoiceStudy AI goes beyond simple Q&A. The **Lyzr Quiz Agent** dynamically pulls stored Qdrant memories and generates 5 active recall revision questions complete with multiple-choice options and detailed explanations."*

---

### 4:20 – 5:00 | Architecture Summary & Hackathon Impact
- **Presenter Action:** Show the **Agent Architecture Pipeline** banner in the UI.
- **Script:**  
  *"In summary, VoiceStudy AI connects **Omi Wearable voice capture**, **Qdrant persistent vector memory**, and **Lyzr agentic reasoning** into one seamless, unified execution loop.  
  It turns passive listening into active, permanent knowledge. Thank you!"*

---

## 🎯 Key Verification Checklist for Video Demo
- [x] Omi webhook endpoint active (`POST /omi/conversation?uid=...`)
- [x] Persistent Qdrant vector storage & deletion
- [x] Grounded Lyzr Agent responses (no fake AI fallbacks)
- [x] Live observable workflow progress panel
- [x] Under 5 minutes total runtime
