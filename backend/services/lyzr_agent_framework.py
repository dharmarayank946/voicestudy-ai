import os
import json
import logging
import httpx
from typing import Dict, Any, Optional, List

logger = logging.getLogger("voicestudy.lyzr")

class LyzrAgentFramework:
    """
    Lyzr Agent & Orchestration Service.
    Configures and coordinates specialized AI agents (Orchestrator, Memory, Assistant, Quiz)
    using Lyzr Agent API architecture with robust fallback execution.
    """
    def __init__(self):
        self.lyzr_api_key = os.getenv("LYZR_API_KEY", "").strip()
        self.llm_api_key = (os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        self.base_url = os.getenv("LYZR_BASE_URL", "https://agent-prod.lyzr.ai").rstrip("/")

        # Specific Lyzr Agent IDs configured per role with fallbacks
        self.agent_ids = {
            "Orchestrator": os.getenv("LYZR_AGENT_ID_ORCHESTRATOR", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip(),
            "Assistant": os.getenv("LYZR_AGENT_ID_ASSISTANT", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip(),
            "Quiz": os.getenv("LYZR_AGENT_ID_QUIZ", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip(),
            "Memory": os.getenv("LYZR_AGENT_ID_MEMORY", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip()
        }

    def get_agent_id(self, agent_name: str) -> str:
        """Get configured Lyzr Agent ID for a given role or return default naming convention."""
        configured_id = self.agent_ids.get(agent_name, "")
        if configured_id:
            return configured_id
        return f"voicestudy_{agent_name.lower().replace(' ', '_')}"

    def get_framework_status(self) -> Dict[str, Any]:
        """Report current Lyzr framework mode, active API keys, and agent ID mappings."""
        if self.lyzr_api_key and self.lyzr_api_key.startswith("lyzr-"):
            mode = "real_lyzr_api"
        elif self.llm_api_key and self.llm_api_key.startswith("sk-"):
            mode = "openai_llm_fallback"
        else:
            mode = "offline_engine_fallback"

        return {
            "mode": mode,
            "lyzr_api_key_configured": bool(self.lyzr_api_key and self.lyzr_api_key.startswith("lyzr-")),
            "openai_api_key_configured": bool(self.llm_api_key and self.llm_api_key.startswith("sk-")),
            "base_url": self.base_url,
            "configured_agent_ids": self.agent_ids
        }

    def execute_agent_prompt(
        self,
        agent_name: str,
        system_instructions: str,
        user_input: str,
        temperature: float = 0.3,
        json_output: bool = False
    ) -> str:
        """
        Execute an agent request using Real Lyzr API if configured, or direct LLM client / offline engine.
        """
        logger.info(f"[LYZR] Agent called: {agent_name} | Input prompt: '{user_input[:80]}...'")
        agent_id = self.get_agent_id(agent_name)

        # 1. Attempt Real Lyzr API call if valid Lyzr key is provided
        if self.lyzr_api_key and self.lyzr_api_key.startswith("lyzr-"):
            try:
                headers = {
                    "x-api-key": self.lyzr_api_key,
                    "Authorization": f"Bearer {self.lyzr_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "user_id": "voicestudy_student",
                    "agent_id": agent_id,
                    "message": f"System Instructions: {system_instructions}\n\nTask/Input: {user_input}"
                }
                logger.info(f"[LYZR] Sending real API request to {self.base_url}/v2/chat (Agent ID: {agent_id})...")
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(f"{self.base_url}/v2/chat", headers=headers, json=payload)
                    if response.status_code in (200, 201):
                        data = response.json()
                        res_text = (
                            data.get("response") or
                            data.get("message") or
                            data.get("output") or
                            (data.get("data", {}).get("response") if isinstance(data.get("data"), dict) else "") or
                            ""
                        )
                        if res_text:
                            logger.info(f"[LYZR] SUCCESS - Real Lyzr API response received for {agent_name} (Agent ID: {agent_id}): '{res_text[:80]}...'")
                            return res_text
                        else:
                            logger.warning(f"[LYZR] Real Lyzr API returned empty text payload for {agent_name}. Falling back.")
                    else:
                        logger.warning(f"[LYZR] Real Lyzr API responded with HTTP {response.status_code}: {response.text[:200]}")
            except Exception as e:
                logger.warning(f"[LYZR] Real Lyzr API call failed for {agent_name}, switching to fallback: {e}")

        # 2. Fallback to OpenAI / LLM provider if API key present
        if self.llm_api_key and self.llm_api_key.startswith("sk-"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.llm_api_key)
                
                messages = [
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_input}
                ]
                
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                }
                if json_output:
                    kwargs["response_format"] = {"type": "json_object"}

                response = client.chat.completions.create(**kwargs)
                res_text = response.choices[0].message.content or ""
                logger.info(f"[LYZR] Response received from {agent_name} via OpenAI LLM: '{res_text[:80]}...'")
                return res_text
            except Exception as e:
                logger.error(f"[LYZR] OpenAI LLM API execution failed: {e}")

        # 3. Local offline deterministic engine fallback (clearly labeled)
        res_text = self._generate_fallback_response(agent_name, user_input, json_output)
        logger.info(f"[LYZR] Response generated for {agent_name} via Local Offline Engine (No valid Lyzr/OpenAI API key configured)")
        return res_text

    def _generate_fallback_response(self, agent_name: str, user_input: str, json_output: bool) -> str:
        """Offline deterministic response generator when API keys are not provided."""
        lower_input = user_input.lower()
        
        if agent_name == "Orchestrator":
            if any(w in lower_input for w in ["explain", "compare", "difference between", "how does", "what is"]):
                intent = "EXPLAIN"
            elif any(w in lower_input for w in ["summarize", "summary", "recent topics", "list topics"]):
                intent = "SUMMARIZE"
            elif any(w in lower_input for w in ["quiz", "test", "question", "questions", "revision"]):
                intent = "QUIZ"
            elif any(w in lower_input for w in ["what did i", "when did i", "show my", "search", "recall"]):
                intent = "RETRIEVE"
            elif any(w in lower_input for w in ["remember", "note", "save", "learned", "studied"]):
                intent = "REMEMBER"
            else:
                intent = "RETRIEVE"

            subject = "DBMS" if any(k in lower_input for k in ["dbms", "database", "sql", "concurrency"]) else \
                      "Computer Networks" if any(k in lower_input for k in ["network", "tcp", "udp", "ip", "protocol"]) else \
                      "Operating Systems" if any(k in lower_input for k in ["os", "operating system", "paging", "process"]) else "Computer Science"

            topic = "Concurrency Control" if "concurrency" in lower_input else \
                    "TCP and UDP" if "tcp" in lower_input or "udp" in lower_input else \
                    "Page Replacement" if "paging" in lower_input or "page" in lower_input else "Study Topic"

            if json_output:
                return json.dumps({
                    "intent": intent,
                    "subject": subject,
                    "topic": topic,
                    "extracted_content": user_input,
                    "reasoning": f"Classified intent as {intent} for subject {subject}"
                })
            return intent

        elif agent_name == "Assistant":
            return f"Based on your study memories regarding your prompt: '{user_input[:100]}'\n\nHere is a structured summary of what you studied:\n- Key Concepts: High level principles, main definitions, and core techniques.\n- Key Takeaway: Regular active recall helps reinforce this material."

        elif agent_name == "Quiz":
            import re
            
            # Extract requested num_questions from prompt (e.g. "Generate exactly 5")
            num_match = re.search(r"Generate exactly (\d+)", user_input, re.IGNORECASE)
            req_count = int(num_match.group(1)) if num_match else 5

            # Extract topic from prompt (e.g. revising: "DBMS Concurrency Control")
            topic_match = re.search(r'revising:\s*"([^"]+)"', user_input, re.IGNORECASE)
            topic_name = topic_match.group(1).strip() if topic_match else "Study Topic"
            
            # Build question pool tailored to topic and study memories
            pool = []
            
            # Question 1
            pool.append({
                "id": 1,
                "question": f"In {topic_name}, what primary mechanism ensures consistent execution?",
                "options": ["Serializability & Locking Protocols", "Checksum Validation", "Memory Allocation", "Packet Routing"],
                "correct_answer": 0,
                "explanation": f"Serializability in {topic_name} guarantees that concurrent execution yields the same state as serial execution."
            })
            
            # Question 2
            pool.append({
                "id": 2,
                "question": f"Which protocol or principle prevents dirty reads when revising {topic_name}?",
                "options": ["Two-Phase Locking (2PL / Strict 2PL)", "UDP Checksum", "B-Tree Indexing", "Sliding Window Protocol"],
                "correct_answer": 0,
                "explanation": f"Strict 2PL prevents uncommitted dirty reads by holding exclusive locks until transaction commit."
            })
            
            # Question 3
            pool.append({
                "id": 3,
                "question": f"Which ACID property guarantees that committed changes in {topic_name} survive system crashes?",
                "options": ["Atomicity", "Consistency", "Isolation", "Durability"],
                "correct_answer": 3,
                "explanation": "Durability guarantees that once a transaction commits, its updates persist permanently."
            })
            
            # Question 4
            pool.append({
                "id": 4,
                "question": f"What is a primary advantage of indexing and structured storage for {topic_name}?",
                "options": ["Reduces disk I/O search complexity to O(log N)", "Eliminates network latency completely", "Guarantees zero memory allocation", "Prevents all deadlocks automatically"],
                "correct_answer": 0,
                "explanation": "Indexes such as B-Trees reduce data lookup time complexity from linear scanning O(N) to log-time O(log N)."
            })
            
            # Question 5
            pool.append({
                "id": 5,
                "question": f"How does active recall and periodic testing reinforce concepts in {topic_name}?",
                "options": ["Strengthens memory retrieval pathways", "Eliminates the need for review", "Replaces initial learning", "Only works for mathematics"],
                "correct_answer": 0,
                "explanation": "Active recall requires retrieving information from memory, strengthening neural connections."
            })
            
            # Additional questions for 10-question requests
            for i in range(6, 11):
                pool.append({
                    "id": i,
                    "question": f"Question {i}: What key trade-off should be evaluated when optimizing {topic_name} (Concept {i-5})?",
                    "options": [
                        "Latency vs Throughput trade-offs",
                        "Hardware cost vs power usage",
                        "Single-thread speed vs disk size",
                        "Compression ratio vs audio frequency"
                    ],
                    "correct_answer": 0,
                    "explanation": f"Optimizing {topic_name} requires balancing lock contention latency against overall system transaction throughput."
                })
                
            selected_questions = pool[:req_count]
            
            if json_output:
                return json.dumps({
                    "title": f"{topic_name} Revision Quiz",
                    "questions": selected_questions
                })
            return f"Generated {len(selected_questions)} revision questions for {topic_name}."

        return f"Processed query by {agent_name}: {user_input}"

lyzr_framework = LyzrAgentFramework()

