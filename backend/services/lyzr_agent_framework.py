import os
import json
import logging
import httpx
from typing import Dict, Any, Optional, List

logger = logging.getLogger("voicestudy.lyzr")

class LyzrAgentFramework:
    """
    Lyzr Agent Framework service supporting genuine AI providers (Lyzr, OpenAI)
    and a robust, multi-subject offline engine.
    """
    def __init__(self):
        self.lyzr_api_key = os.getenv("LYZR_API_KEY", "").strip()
        self.llm_api_key = (os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        self.base_url = os.getenv("LYZR_BASE_URL", "https://agent-prod.lyzr.ai").rstrip("/")

        self.agent_ids = {
            "Orchestrator": os.getenv("LYZR_AGENT_ID_ORCHESTRATOR", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip(),
            "Assistant": os.getenv("LYZR_AGENT_ID_ASSISTANT", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip(),
            "Quiz": os.getenv("LYZR_AGENT_ID_QUIZ", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip(),
            "Memory": os.getenv("LYZR_AGENT_ID_MEMORY", "").strip() or os.getenv("LYZR_AGENT_ID", "").strip()
        }

    def get_agent_id(self, agent_name: str) -> str:
        configured_id = self.agent_ids.get(agent_name, "")
        if configured_id:
            return configured_id
        return f"voicestudy_{agent_name.lower().replace(' ', '_')}"

    def get_framework_status(self) -> Dict[str, Any]:
        if self.lyzr_api_key and self.lyzr_api_key.startswith("lyzr-"):
            mode = "real_lyzr_api"
            is_real_ai = True
            provider_name = "Lyzr AI Platform"
        elif self.llm_api_key and self.llm_api_key.startswith("sk-"):
            mode = "openai_llm_fallback"
            is_real_ai = True
            provider_name = "OpenAI API"
        else:
            mode = "offline_engine_fallback"
            is_real_ai = False
            provider_name = "Offline Engine Fallback"

        return {
            "mode": mode,
            "is_real_ai": is_real_ai,
            "provider_name": provider_name,
            "lyzr_api_key_configured": bool(self.lyzr_api_key and self.lyzr_api_key.startswith("lyzr-")),
            "openai_api_key_configured": bool(self.llm_api_key and self.llm_api_key.startswith("sk-")),
            "base_url": self.base_url,
            "configured_agent_ids": self.agent_ids,
            "notice": "Connected to Genuine AI Provider" if is_real_ai else "Offline Engine Mode: No API key configured. Providing curated subject knowledge."
        }

    def execute_agent_prompt(
        self,
        agent_name: str,
        system_instructions: str,
        user_input: str,
        temperature: float = 0.3,
        json_output: bool = False
    ) -> str:
        logger.info(f"[LYZR] Agent called: {agent_name} | Input prompt: '{user_input[:80]}...'")
        agent_id = self.get_agent_id(agent_name)

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
                            logger.info(f"[LYZR] SUCCESS - Real Lyzr API response received for {agent_name}")
                            return res_text
            except Exception as e:
                logger.warning(f"[LYZR] Real Lyzr API call failed for {agent_name}: {e}")

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
                return res_text
            except Exception as e:
                logger.error(f"[LYZR] OpenAI LLM API execution failed: {e}")

        res_text = self._generate_fallback_response(agent_name, user_input, json_output)
        return res_text

    def _generate_fallback_response(self, agent_name: str, user_input: str, json_output: bool) -> str:
        lower_input = user_input.lower()
        
        if agent_name == "Orchestrator":
            if any(w in lower_input for w in ["explain", "compare", "difference between", "how does", "what is", "describe", "why"]):
                intent = "EXPLAIN"
            elif any(w in lower_input for w in ["summarize", "summary", "recent topics", "list topics", "overview"]):
                intent = "SUMMARIZE"
            elif any(w in lower_input for w in ["quiz", "test", "question", "questions", "revision"]):
                intent = "QUIZ"
            elif any(w in lower_input for w in ["what did i", "when did i", "show my", "search", "recall"]):
                intent = "RETRIEVE"
            elif any(w in lower_input for w in ["remember", "note", "save", "learned", "studied"]):
                intent = "REMEMBER"
            else:
                intent = "EXPLAIN"

            if any(k in lower_input for k in ["math", "calculus", "linear algebra", "matrix", "vector", "probability", "derivative", "integral"]):
                subject = "Mathematics"
            elif any(k in lower_input for k in ["solid", "design pattern", "agile", "scrum", "software engineering", "refactoring", "microservices", "unit test"]):
                subject = "Software Engineering"
            elif any(k in lower_input for k in ["operating system", "paging", "process", "thread", "deadlock", "cpu schedule", "virtual memory", "kernel"]):
                subject = "Operating Systems"
            elif any(k in lower_input for k in ["dbms", "database", "sql", "concurrency", "2pl", "acid", "transaction", "index"]):
                subject = "DBMS"
            elif any(k in lower_input for k in ["network", "tcp", "udp", "ip address", "tcp/ip", "protocol", "dns", "http", "osi", "router", "socket"]):
                subject = "Computer Networks"
            elif any(k in lower_input for k in ["python", "java", "c++", "programming", "data structure", "algorithm", "async", "array", "recursion"]):
                subject = "Programming"
            else:
                subject = "General Study"

            topic = "General Concept"
            if "concurrency" in lower_input: topic = "Concurrency Control"
            elif "paging" in lower_input or "virtual memory" in lower_input: topic = "Virtual Memory & Paging"
            elif "tcp" in lower_input or "udp" in lower_input: topic = "TCP vs UDP"
            elif "solid" in lower_input: topic = "SOLID Principles"
            elif "design pattern" in lower_input: topic = "Design Patterns"
            elif "process" in lower_input or "thread" in lower_input: topic = "Processes & Threads"
            elif "python" in lower_input: topic = "Python Core Concepts"

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
            return self._build_offline_assistant_answer(user_input)

        elif agent_name == "Quiz":
            import re
            num_match = re.search(r"Generate exactly (\d+)", user_input, re.IGNORECASE)
            req_count = int(num_match.group(1)) if num_match else 5

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

    def _build_offline_assistant_answer(self, user_input: str) -> str:
        q_lower = user_input.lower()
        notice = "> ⚡ **Offline Engine Fallback**: Intelligent AI provider API key is not configured. Displaying curated subject knowledge.\n\n"

        # 1. Mathematics
        if any(k in q_lower for k in ["matrix", "linear algebra", "vector", "calculus", "derivative", "integral", "eigenvalue"]):
            return notice + "### Mathematics: Fundamentals for Computer Science\n\n" \
                   "- **Linear Algebra**: Vectors and matrices model spatial transformations, system equations, and machine learning weights.\n" \
                   "- **Calculus**: Derivatives quantify change rates powering optimization techniques like Gradient Descent, while integrals compute continuous totals.\n" \
                   "- **Matrix Multiplication**: Inner product of row vectors by column vectors transforming coordinate bases across vector spaces.\n" \
                   "- **Practical Example**: 3D computer graphics engines use 4x4 transformation matrices to project 3D object vertices onto 2D screen coordinates."

        # 2. Software Engineering
        if any(k in q_lower for k in ["solid", "design principle", "single responsibility", "liskov", "dependency inversion"]):
            return notice + "### Software Engineering: SOLID Principles\n\n" \
                   "- **Single Responsibility**: Each class has one clear responsibility and reason to change.\n" \
                   "- **Open/Closed**: Software entities are open for extension but closed for direct modification.\n" \
                   "- **Liskov Substitution**: Subclasses must be transparently substitutable for their parent classes.\n" \
                   "- **Interface Segregation**: Prefer small, focused interfaces over bulky monolithic ones.\n" \
                   "- **Dependency Inversion**: High-level modules depend on abstractions rather than low-level concrete implementations.\n" \
                   "- **Practical Example**: Defining interface abstractions for external integrations allows swapping service providers without rewriting core logic."

        if any(k in q_lower for k in ["design pattern", "factory", "singleton", "observer", "adapter", "decorator"]):
            return notice + "### Software Engineering: Key Design Patterns\n\n" \
                   "- **Creational**: Factory Method and Singleton encapsulate object creation.\n" \
                   "- **Structural**: Adapter and Decorator dynamically compose complex structures.\n" \
                   "- **Behavioral**: Observer and Strategy coordinate algorithm execution and event notifications.\n" \
                   "- **Practical Example**: The **Observer Pattern** allows event producers to automatically notify registered UI listeners on state updates."

        # 3. Operating Systems
        if any(k in q_lower for k in ["virtual memory", "paging", "page fault", "tlb"]):
            return notice + "### Operating Systems: Virtual Memory & Paging\n\n" \
                   "- **Core Concept**: Virtual Memory separates physical RAM from logical process address space using fixed-size Paging.\n" \
                   "- **Key Mechanism**: When a requested page is absent from RAM, a **Page Fault** exception triggers the OS kernel to load it from disk.\n" \
                   "- **Hardware Accelerator**: The **Translation Lookaside Buffer (TLB)** caches virtual-to-physical address mappings for fast access.\n" \
                   "- **Practical Example**: Modern OS environments execute large applications on modest hardware by dynamically swapping memory pages."

        if any(k in q_lower for k in ["process", "thread", "context switch"]):
            return notice + "### Operating Systems: Processes vs Threads\n\n" \
                   "- **Process**: Isolated executing program containing its own memory address space, heap, and Process Control Block (PCB).\n" \
                   "- **Thread**: Lightweight unit of execution within a process sharing memory and heap, with an independent execution stack.\n" \
                   "- **Context Switch**: The OS saves register states to toggle CPU execution. Thread context switching is significantly faster than process switching."

        if any(k in q_lower for k in ["deadlock", "coffman", "banker"]):
            return notice + "### Operating Systems: Deadlock Prevention & Handling\n\n" \
                   "- **Definition**: A deadlock occurs when a set of processes are blocked indefinitely waiting for resources held by one another.\n" \
                   "- **Coffman Conditions**: Mutual Exclusion, Hold & Wait, No Preemption, and Circular Wait.\n" \
                   "- **Prevention**: Resource allocation algorithms like **Banker's Algorithm** prevent deadlock states by keeping the system in a safe state."

        # 4. Computer Networks
        if any(k in q_lower for k in ["tcp", "udp"]):
            return notice + "### Computer Networks: TCP vs UDP Transport Protocols\n\n" \
                   "- **TCP**: Connection-oriented, reliable, guarantees ordered delivery using 3-way handshakes and flow/congestion control.\n" \
                   "- **UDP**: Connectionless, lightweight datagram protocol with low overhead and minimal latency.\n" \
                   "- **Practical Example**: Web traffic (HTTP/HTTPS) relies on TCP; live video streaming and gaming use UDP."

        if any(k in q_lower for k in ["osi", "layer", "router", "switch", "mac address"]):
            return notice + "### Computer Networks: 7-Layer OSI Reference Model\n\n" \
                   "1. **Physical**: Raw bitstream transmission over physical media.\n" \
                   "2. **Data Link**: MAC address node-to-node framing.\n" \
                   "3. **Network**: IP packet routing across network paths.\n" \
                   "4. **Transport**: Host-to-host end-to-end communication (TCP/UDP).\n" \
                   "5. **Session**: Manages multi-connection sessions.\n" \
                   "6. **Presentation**: Data formatting, encryption, and compression.\n" \
                   "7. **Application**: Network application interface (HTTP, DNS, SSH)."

        # 5. DBMS (Only matched when explicit DBMS terms are in query)
        if any(k in q_lower for k in ["dbms", "database", "2pl", "concurrency control", "acid", "sql", "transaction lock"]):
            return notice + "### DBMS: Concurrency Control & Two-Phase Locking (2PL)\n\n" \
                   "- **ACID Isolation**: Prevents concurrent transaction anomalies (dirty reads, phantom reads).\n" \
                   "- **2PL Protocol**: Features a Growing Phase (acquiring locks) and Shrinking Phase (releasing locks).\n" \
                   "- **Strict 2PL**: Holds exclusive locks until commit/abort to eliminate cascading aborts.\n" \
                   "- **Practical Example**: Banking systems use Strict 2PL to prevent uncommitted fund transfers from being read by concurrent queries."

        # 6. Programming
        if any(k in q_lower for k in ["python", "gil", "async"]):
            return notice + "### Programming: Python Core Execution & Concurrency\n\n" \
                   "- **GIL**: Global Interpreter Lock prevents parallel execution of Python bytecodes in a single CPython process.\n" \
                   "- **Concurrency**: Use `multiprocessing` for CPU-intensive workloads and `asyncio` for non-blocking I/O tasks."

        if any(k in q_lower for k in ["data structure", "algorithm", "array", "tree", "graph", "sorting", "searching"]):
            return notice + "### Data Structures & Algorithms Overview\n\n" \
                   "- **Arrays & Hash Tables**: Direct index or hashed key access with O(1) time complexity.\n" \
                   "- **Trees & Graphs**: Hierarchical/linked structures navigated using BFS or DFS algorithms.\n" \
                   "- **Big-O Notation**: Quantifies execution scaling relative to input volume."

        # 7. Open-Ended / General Knowledge Fallback
        import re
        clean_q = re.sub(r'^(STUDENT QUESTION:|Explain|What is|What are|Describe|How does|Tell me about)\s*', '', user_input, flags=re.IGNORECASE).strip(' "?.\'')
        topic_title = clean_q.title() if clean_q else "General Knowledge Concept"

        return notice + f"### Explanation: {topic_title}\n\n" \
               f"- **Core Concept**: Core principles, fundamental definitions, and foundational rules governing **{topic_title}**.\n" \
               f"- **Key Mechanism**: Primary operational workflow, step-by-step processing, and component interactions.\n" \
               f"- **Practical Application**: Implementing and applying **{topic_title}** effectively in software systems and real-world domain scenarios.\n" \
               f"- **Practical Example**: Real-world implementation demonstrating **{topic_title}** principles in action with clear outcomes."

    def _build_topic_quiz_pool(self, topic_name: str, req_count: int, user_input: str = "") -> List[Dict[str, Any]]:
        topic_lower = topic_name.lower()
        search_text = topic_lower if topic_lower not in ["recent studies", "study topic", "general", ""] else (topic_name + " " + user_input).lower()
        
        if any(k in search_text for k in ["solid", "software engineering", "design pattern", "agile"]):
            pool = [
                {
                    "id": 1,
                    "question": f"In {topic_name}, what does the Single Responsibility Principle state?",
                    "options": [
                        "A class should have only one reason to change",
                        "A class should contain all application business logic in one place",
                        "A method should execute in a single thread only",
                        "A database table should hold only one primary key column"
                    ],
                    "correct_answer": 0,
                    "explanation": "Single Responsibility ensures high cohesion by restricting a class to one responsibility."
                },
                {
                    "id": 2,
                    "question": f"Which design pattern in {topic_name} provides a surrogate or placeholder for another object to control access?",
                    "options": [
                        "Proxy Pattern",
                        "Singleton Pattern",
                        "Factory Method Pattern",
                        "Observer Pattern"
                    ],
                    "correct_answer": 0,
                    "explanation": "Proxy controls access to the original object, enabling lazy initialization or access control."
                }
            ]
            for i in range(3, 11):
                pool.append({
                    "id": i,
                    "question": f"In {topic_name} (Concept {i}), what is the main benefit of Dependency Inversion?",
                    "options": [
                        "Decoupling high-level modules from low-level implementation details via abstractions",
                        "Increasing CPU clock speeds during execution",
                        "Reducing network latency in web API requests",
                        "Automatically indexing database tables"
                    ],
                    "correct_answer": 0,
                    "explanation": "Dependency Inversion allows software components to depend on interfaces rather than concrete classes."
                })
            return pool[:req_count]

        elif any(k in search_text for k in ["network", "tcp", "udp", "ip", "protocol"]):
            pool = [
                {
                    "id": 1,
                    "question": f"In {topic_name}, what mechanism does TCP use to establish a reliable connection?",
                    "options": [
                        "Three-way handshake (SYN, SYN-ACK, ACK)",
                        "Random UDP datagram broadcast",
                        "DNS host resolution query",
                        "HTTP GET request header exchange"
                    ],
                    "correct_answer": 0,
                    "explanation": "TCP establishes connection parameters using the 3-way handshake before transmitting data."
                },
                {
                    "id": 2,
                    "question": f"How does UDP differ from TCP in {topic_name}?",
                    "options": [
                        "UDP is connectionless and does not guarantee packet delivery order",
                        "UDP guarantees packet ordering but operates at slower speeds",
                        "UDP works only over physical fiber optic cables",
                        "UDP encrypts all packet payloads by default"
                    ],
                    "correct_answer": 0,
                    "explanation": "UDP provides fast, connectionless transmission without delivery guarantees."
                }
            ]
            for i in range(3, 11):
                pool.append({
                    "id": i,
                    "question": f"In {topic_name} (Concept {i}), which layer of the OSI model handles end-to-end communication?",
                    "options": [
                        "Transport Layer (Layer 4)",
                        "Network Layer (Layer 3)",
                        "Data Link Layer (Layer 2)",
                        "Application Layer (Layer 7)"
                    ],
                    "correct_answer": 0,
                    "explanation": "Transport layer provides host-to-host communication services for applications."
                })
            return pool[:req_count]

        elif any(k in search_text for k in ["os", "operating system", "paging", "memory", "process", "thread"]):
            pool = [
                {
                    "id": 1,
                    "question": f"In {topic_name}, what event occurs when a requested page is not present in physical RAM?",
                    "options": [
                        "Page Fault interrupt",
                        "Deadlock exception",
                        "Segmentation fault crash",
                        "Checksum mismatch"
                    ],
                    "correct_answer": 0,
                    "explanation": "A page fault signals the OS to retrieve the missing page from disk into RAM."
                },
                {
                    "id": 2,
                    "question": f"Which page replacement algorithm yields the theoretical minimum page fault rate in {topic_name}?",
                    "options": [
                        "Optimal Page Replacement (Belady's Algorithm)",
                        "First-In First-Out (FIFO)",
                        "Least Recently Used (LRU)",
                        "Second Chance Page Replacement"
                    ],
                    "correct_answer": 0,
                    "explanation": "Optimal page replacement replaces the page that will not be used for the longest future duration."
                }
            ]
            for i in range(3, 11):
                pool.append({
                    "id": i,
                    "question": f"In {topic_name} (Concept {i}), what information is saved during an OS context switch?",
                    "options": [
                        "CPU registers, Program Counter, and Process Control Block (PCB)",
                        "User interface configuration parameters",
                        "Application log files",
                        "Disk partition tables"
                    ],
                    "correct_answer": 0,
                    "explanation": "A context switch saves process register states and program counter to PCB."
                })
            return pool[:req_count]

        pool = [
            {
                "id": 1,
                "question": f"In {topic_name}, what is the primary goal of concurrency control?",
                "options": [
                    "Ensuring serializability of concurrent transactions",
                    "Executing queries in single-user mode",
                    "Translating SQL queries to disk offsets",
                    "Reverting database schema changes"
                ],
                "correct_answer": 0,
                "explanation": "Concurrency control ensures concurrent transaction execution yields a state equivalent to serial execution."
            },
            {
                "id": 2,
                "question": f"What defines the Two-Phase Locking (2PL) protocol in {topic_name}?",
                "options": [
                    "A growing phase to acquire locks, followed by a shrinking phase to release locks",
                    "Executing transactions twice before commit",
                    "Locking tables for fixed 2-second intervals",
                    "Splitting operations into two transactions"
                ],
                "correct_answer": 0,
                "explanation": "Under 2PL, a transaction cannot acquire any new locks once it releases its first lock."
            },
            {
                "id": 3,
                "question": f"In {topic_name}, how does a Shared (S) lock differ from an Exclusive (X) lock?",
                "options": [
                    "Shared locks allow concurrent reads, while Exclusive locks grant single-transaction write access",
                    "Shared locks allow writing, while Exclusive locks block all access",
                    "Shared locks apply only to views, while Exclusive locks apply to tables",
                    "Exclusive locks expire instantly upon acquisition"
                ],
                "correct_answer": 0,
                "explanation": "Multiple transactions can hold Shared locks to read data, but an Exclusive lock requires sole access."
            },
            {
                "id": 4,
                "question": f"How does Strict Two-Phase Locking (Strict 2PL) handle exclusive locks to avoid cascading aborts?",
                "options": [
                    "All exclusive locks are held until transaction completion and commit",
                    "Locks are released immediately after writing to buffer pool",
                    "Exclusive locks are shared with background indexers",
                    "Locks expire automatically after 100 milliseconds"
                ],
                "correct_answer": 0,
                "explanation": "Holding exclusive locks until commit guarantees that uncommitted data is never read by other transactions."
            },
            {
                "id": 5,
                "question": f"In {topic_name}, what condition triggers a deadlock between concurrent transactions?",
                "options": [
                    "Circular dependency where transactions wait indefinitely for resources held by each other",
                    "Writing to index files faster than disk throughput",
                    "Executing SELECT queries on unindexed columns",
                    "Running multiple read operations concurrently"
                ],
                "correct_answer": 0,
                "explanation": "Deadlocks occur when two or more transactions hold locks and request locks held by one another in a cycle."
            },
            {
                "id": 6,
                "question": f"Which isolation level prevents Dirty Reads but permits Non-repeatable Reads in {topic_name}?",
                "options": [
                    "Read Committed",
                    "Read Uncommitted",
                    "Repeatable Read",
                    "Serializable"
                ],
                "correct_answer": 0,
                "explanation": "Read Committed ensures transactions read only committed changes, preventing dirty reads."
            },
            {
                "id": 7,
                "question": f"In {topic_name}, what does the Atomicity property of ACID guarantee?",
                "options": [
                    "All operations in a transaction execute successfully or none at all (all-or-nothing)",
                    "Data is duplicated across multiple disk arrays instantly",
                    "Queries run with 0 millisecond latency",
                    "Transactions execute in alphabetical order by table name"
                ],
                "correct_answer": 0,
                "explanation": "Atomicity ensures partial execution of a transaction never persists to the database."
            },
            {
                "id": 8,
                "question": f"What mechanism detects deadlocks by periodically searching for cycles in {topic_name}?",
                "options": [
                    "Wait-For Graph (WFG) cycle detection algorithm",
                    "B-Tree index traversal",
                    "LRU page eviction scanner",
                    "Checksum hash validation"
                ],
                "correct_answer": 0,
                "explanation": "A Wait-For Graph tracks transaction wait dependencies and identifies cycles to break deadlocks."
            },
            {
                "id": 9,
                "question": f"In {topic_name}, what timestamp-ordering rule prevents old transactions from overwriting newer writes?",
                "options": [
                    "Thomas Write Rule",
                    "Belady's Anomaly Detection",
                    "Peterson's Algorithm",
                    "Dijkstra's Shortest Path Rule"
                ],
                "correct_answer": 0,
                "explanation": "Thomas Write Rule ignores outdated write operations if a newer transaction has already written the item."
            },
            {
                "id": 10,
                "question": f"How does Rigorous Two-Phase Locking differ from Strict 2PL in {topic_name}?",
                "options": [
                    "Rigorous 2PL holds ALL locks (both shared and exclusive) until transaction commit",
                    "Rigorous 2PL releases locks before the growing phase ends",
                    "Rigorous 2PL eliminates the need for database logging",
                    "Rigorous 2PL only operates on in-memory table structures"
                ],
                "correct_answer": 0,
                "explanation": "Rigorous 2PL retains all locks (read and write) until commit, ensuring serializable schedules."
            }
        ]
        return pool[:req_count]

lyzr_framework = LyzrAgentFramework()
