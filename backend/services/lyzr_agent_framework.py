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
            
            selected_questions = self._build_topic_quiz_pool(topic_name, req_count, user_input)
            
            if json_output:
                return json.dumps({
                    "title": f"{topic_name} Revision Quiz",
                    "questions": selected_questions
                })
            return f"Generated {len(selected_questions)} revision questions for {topic_name}."

        return f"Processed query by {agent_name}: {user_input}"

    def _build_topic_quiz_pool(self, topic_name: str, req_count: int, user_input: str = "") -> List[Dict[str, Any]]:
        """Build highly accurate topic-specific question banks for offline execution."""
        topic_lower = topic_name.lower()
        search_text = topic_lower if topic_lower not in ["recent studies", "study topic", "general", ""] else (topic_name + " " + user_input).lower()
        
        # 1. DBMS & Concurrency Control Bank
        if any(k in search_text for k in ["dbms", "concurrency", "transaction", "database", "2pl", "lock", "acid"]):
            pool = [
                {
                    "id": 1,
                    "question": f"In {topic_name}, what is the primary goal of concurrency control?",
                    "options": [
                        "Ensuring serializability of concurrent transactions",
                        "Executing all database queries sequentially in single-user mode",
                        "Translating SQL queries into physical disk block offsets",
                        "Reverting database schema changes automatically on startup"
                    ],
                    "correct_answer": 0,
                    "explanation": "Concurrency control ensures that concurrent execution of transactions yields a database state equivalent to serial execution."
                },
                {
                    "id": 2,
                    "question": f"In {topic_name}, how do Shared (S) and Exclusive (X) locks differ?",
                    "options": [
                        "Shared locks allow multiple concurrent readers; Exclusive locks permit only one writer",
                        "Exclusive locks allow unlimited readers; Shared locks permit only one writer",
                        "Shared locks automatically commit transactions; Exclusive locks abort them",
                        "Both Shared and Exclusive locks allow concurrent writing without restriction"
                    ],
                    "correct_answer": 0,
                    "explanation": "Shared locks can be held simultaneously by multiple transactions for reading, whereas Exclusive locks grant exclusive write access."
                },
                {
                    "id": 3,
                    "question": f"What defines the Two-Phase Locking (2PL) protocol in {topic_name}?",
                    "options": [
                        "A growing phase where locks are acquired, followed by a shrinking phase where locks are released",
                        "Executing transactions twice to verify consistency before commit",
                        "Locking database tables for fixed 2-second time intervals",
                        "Splitting single SQL operations into two separate transactions"
                    ],
                    "correct_answer": 0,
                    "explanation": "Under 2PL, a transaction cannot acquire any new locks once it has released its first lock."
                },
                {
                    "id": 4,
                    "question": f"How does Strict Two-Phase Locking (Strict 2PL) prevent cascading aborts in {topic_name}?",
                    "options": [
                        "By holding all Exclusive locks until the transaction commits or aborts",
                        "By releasing locks immediately after every SQL SELECT query",
                        "By disabling all concurrent transactions entirely",
                        "By forcing all write operations to execute in separate threads"
                    ],
                    "correct_answer": 0,
                    "explanation": "Strict 2PL prevents uncommitted dirty reads by retaining all exclusive locks until transaction completion."
                },
                {
                    "id": 5,
                    "question": f"In {topic_name}, what condition describes a deadlock between transactions?",
                    "options": [
                        "Two or more transactions wait indefinitely for locks held by each other",
                        "A transaction reads data that has already been committed by another transaction",
                        "A query execution time exceeds the database timeout threshold",
                        "The database transaction manager runs out of transaction identifiers"
                    ],
                    "correct_answer": 0,
                    "explanation": "Deadlock occurs when transactions form a cycle in the Wait-For Graph, each waiting for a lock held by another."
                },
                {
                    "id": 6,
                    "question": f"Which transaction isolation level in {topic_name} prevents dirty reads, non-repeatable reads, and phantom reads?",
                    "options": [
                        "Serializable",
                        "Read Committed",
                        "Read Uncommitted",
                        "Repeatable Read"
                    ],
                    "correct_answer": 0,
                    "explanation": "Serializable isolation provides the highest level of isolation, preventing all concurrency anomalies including phantom reads."
                },
                {
                    "id": 7,
                    "question": f"Which ACID property in {topic_name} guarantees that execution of concurrent transactions yields a state equivalent to serial execution?",
                    "options": [
                        "Isolation",
                        "Atomicity",
                        "Consistency",
                        "Durability"
                    ],
                    "correct_answer": 0,
                    "explanation": "Isolation ensures that concurrent transaction execution appears isolated and serializable."
                },
                {
                    "id": 8,
                    "question": f"How does the Timestamp Ordering protocol enforce serializability in {topic_name}?",
                    "options": [
                        "Transactions are ordered strictly by their unique logical timestamps",
                        "Transactions are ordered by execution request order",
                        "Locks are assigned randomly by the operating system",
                        "All write operations are deferred until system shutdown"
                    ],
                    "correct_answer": 0,
                    "explanation": "Timestamp Ordering resolves conflicts by ensuring transactions execute in strict timestamp order."
                },
                {
                    "id": 9,
                    "question": f"What is a primary cause of cascading aborts in a database schedule for {topic_name}?",
                    "options": [
                        "A transaction reads uncommitted data written by another transaction that subsequently aborts",
                        "A database table is altered while a query is running",
                        "A transaction releases a shared lock before completing its read operation",
                        "The transaction manager fails to flush dirty log records"
                    ],
                    "correct_answer": 0,
                    "explanation": "If Transaction A reads dirty data from Transaction B, and Transaction B aborts, Transaction A must also abort (cascading abort)."
                },
                {
                    "id": 10,
                    "question": f"In {topic_name}, what role does the Write-Ahead Logging (WAL) protocol play in transaction recovery?",
                    "options": [
                        "Ensures log records are written to persistent storage before data modifications are flushed",
                        "Deletes all transaction history immediately after commit",
                        "Compresses database data pages to reduce disk storage",
                        "Prevents transaction aborts by auto-committing uncommitted modifications"
                    ],
                    "correct_answer": 0,
                    "explanation": "WAL guarantees durability and atomicity by recording change logs on stable storage prior to flushing dirty pages."
                }
            ]
            return pool[:req_count]

        # 2. Computer Networks & Protocols Bank
        elif any(k in search_text for k in ["network", "tcp", "udp", "protocol", "ip", "socket"]):
            pool = [
                {
                    "id": 1,
                    "question": f"In {topic_name}, what mechanism does TCP use to establish a reliable connection?",
                    "options": [
                        "Three-way handshake (SYN, SYN-ACK, ACK)",
                        "UDP datagram broadcast",
                        "CSMA/CD carrier sensing",
                        "Linear list scan"
                    ],
                    "correct_answer": 0,
                    "explanation": "TCP establishes connection state via a three-way handshake before transmitting application data."
                },
                {
                    "id": 2,
                    "question": f"In {topic_name}, what is a key difference between TCP and UDP?",
                    "options": [
                        "TCP is connection-oriented and reliable; UDP is connectionless and lightweight",
                        "UDP guarantees ordered delivery; TCP does not",
                        "TCP operates at the physical layer; UDP operates at the application layer",
                        "UDP uses a 20-byte mandatory header; TCP uses 8 bytes"
                    ],
                    "correct_answer": 0,
                    "explanation": "TCP provides reliable, ordered stream delivery while UDP sends connectionless datagrams with lower latency."
                },
                {
                    "id": 3,
                    "question": f"How does TCP flow control protect the receiver in {topic_name}?",
                    "options": [
                        "Using a sliding window mechanism based on the receiver's advertised window size",
                        "By dropping packets randomly when receiver buffer is 50% full",
                        "By increasing sender packet size dynamically",
                        "By switching transport protocols to UDP automatically"
                    ],
                    "correct_answer": 0,
                    "explanation": "Flow control prevents a fast sender from overwhelming a slow receiver by adhering to the advertised receive window."
                },
                {
                    "id": 4,
                    "question": f"In {topic_name}, what algorithms does TCP use for congestion control?",
                    "options": [
                        "Slow Start, Congestion Avoidance, Fast Retransmit, and Fast Recovery",
                        "Stop-and-Wait ARQ only",
                        "Round-Robin packet distribution",
                        "Static bandwidth reservation"
                    ],
                    "correct_answer": 0,
                    "explanation": "TCP manages network congestion dynamically using Slow Start and Congestion Avoidance algorithms."
                },
                {
                    "id": 5,
                    "question": f"At which OSI model layer do TCP and UDP operate in {topic_name}?",
                    "options": [
                        "Transport Layer (Layer 4)",
                        "Network Layer (Layer 3)",
                        "Data Link Layer (Layer 2)",
                        "Application Layer (Layer 7)"
                    ],
                    "correct_answer": 0,
                    "explanation": "TCP and UDP are Transport Layer protocols providing end-to-end communication services."
                }
            ]
            for i in range(6, 11):
                pool.append({
                    "id": i,
                    "question": f"In {topic_name} (Concept {i}), what is the primary role of port numbers?",
                    "options": [
                        "Process-to-process multiplexing and demultiplexing on a host",
                        "Identifying physical network interface card addresses",
                        "Encrypting IP packet payloads",
                        "Allocating memory to network socket buffers"
                    ],
                    "correct_answer": 0,
                    "explanation": "Port numbers identify specific application processes running on a host machine."
                })
            return pool[:req_count]

        # 3. Operating Systems Bank
        elif any(k in search_text for k in ["os", "operating system", "paging", "memory", "process"]):
            pool = [
                {
                    "id": 1,
                    "question": f"In {topic_name}, what event occurs when a requested page is not present in physical RAM?",
                    "options": [
                        "Page Fault interrupt",
                        "Deadlock exception",
                        "Segmentation fault crash",
                        "Bitwise checksum mismatch"
                    ],
                    "correct_answer": 0,
                    "explanation": "A page fault signals the OS to retrieve the missing page from backing store into physical memory."
                },
                {
                    "id": 2,
                    "question": f"Which page replacement algorithm in {topic_name} yields the theoretical minimum page fault rate?",
                    "options": [
                        "Optimal Page Replacement (Belady's Algorithm)",
                        "First-In First-Out (FIFO)",
                        "Least Recently Used (LRU)",
                        "Second Chance Page Replacement"
                    ],
                    "correct_answer": 0,
                    "explanation": "Optimal page replacement replaces the page that will not be used for the longest future duration."
                },
                {
                    "id": 3,
                    "question": f"In {topic_name}, what is the purpose of the Translation Lookaside Buffer (TLB)?",
                    "options": [
                        "High-speed hardware cache for page table virtual-to-physical address translations",
                        "Buffer for incoming storage operations",
                        "Queue for CPU thread scheduling",
                        "Cache for application configuration parameters"
                    ],
                    "correct_answer": 0,
                    "explanation": "TLB caches address translations to avoid multi-level page table lookups in RAM."
                },
                {
                    "id": 4,
                    "question": f"In {topic_name}, what causes system thrashing?",
                    "options": [
                        "High page swapping activity when physical RAM is insufficient for process working sets",
                        "High CPU utilization during arithmetic operations",
                        "Excessive disk fragmentation",
                        "Using binary semaphores instead of mutexes"
                    ],
                    "correct_answer": 0,
                    "explanation": "Thrashing occurs when the system spends more time swapping pages in/out than executing instructions."
                },
                {
                    "id": 5,
                    "question": f"Which of the following is NOT one of Coffman's four necessary conditions for deadlock in {topic_name}?",
                    "options": [
                        "Preemption allowed",
                        "Mutual Exclusion",
                        "Hold and Wait",
                        "Circular Wait"
                    ],
                    "correct_answer": 0,
                    "explanation": "Deadlock requires No Preemption (resources cannot be forcibly confiscated from a process)."
                }
            ]
            for i in range(6, 11):
                pool.append({
                    "id": i,
                    "question": f"In {topic_name} (Concept {i}), what state information is saved during an OS context switch?",
                    "options": [
                        "CPU registers, Program Counter, and Process Control Block (PCB)",
                        "Application state log records",
                        "User interface configuration options",
                        "Input/Output buffer handles"
                    ],
                    "correct_answer": 0,
                    "explanation": "A context switch saves process register states and program counter into the PCB to resume execution later."
                })
            return pool[:req_count]

        # 4. Default / General Topic Bank
        pool = []
        for i in range(1, req_count + 1):
            pool.append({
                "id": i,
                "question": f"In {topic_name}, what is Question {i}'s fundamental principle?",
                "options": [
                    f"Core concept {i} of {topic_name}",
                    f"Secondary property {i} of {topic_name}",
                    f"Alternative formulation {i} of {topic_name}",
                    f"Implementation detail {i} of {topic_name}"
                ],
                "correct_answer": 0,
                "explanation": f"Question {i} evaluates key principles directly relevant to {topic_name}."
            })
        return pool
lyzr_framework = LyzrAgentFramework()

