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
            if json_output:
                return json.dumps({
                    "questions": [
                        {
                            "id": 1,
                            "question": f"What is the fundamental concept behind {user_input[:40]}?",
                            "options": ["Concurrency Control", "ACID Properties", "Deadlock Prevention", "Serializability"],
                            "correct_answer": 0,
                            "explanation": "Concurrency control ensures database transactions execute concurrently without violating data integrity."
                        },
                        {
                            "id": 2,
                            "question": "Which protocol prevents dirty reads in database management systems?",
                            "options": ["Two-Phase Locking (2PL)", "UDP Checksum", "B-Tree Indexing", "Sliding Window"],
                            "correct_answer": 0,
                            "explanation": "Two-Phase Locking (2PL) guarantees serializability and prevents dirty reads."
                        },
                        {
                            "id": 3,
                            "question": "What is a primary distinction when comparing TCP and UDP protocols?",
                            "options": ["TCP is connection-oriented; UDP is connectionless", "UDP guarantees packet delivery", "TCP has higher speed and zero overhead", "UDP performs three-way handshakes"],
                            "correct_answer": 0,
                            "explanation": "TCP provides reliable, ordered, connection-oriented data transfer while UDP is lightweight and connectionless."
                        }
                    ]
                })
            return "1. What is the main principle of concurrency control?\n2. Compare 2PL and Timestamp Ordering."

        return f"Processed query by {agent_name}: {user_input}"

lyzr_framework = LyzrAgentFramework()

