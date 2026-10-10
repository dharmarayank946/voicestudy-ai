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

        # 1. Science & Biology (Photosynthesis, Plants, Solar conversion)
        if any(k in q_lower for k in ["photosynthesis", "chlorophyll", "plant food", "sunlight water"]):
            return "Photosynthesis is the process by which green plants use sunlight, water, and carbon dioxide to make their food. Oxygen is released into the atmosphere during this process.\n\n" \
                   "### How Photosynthesis Works:\n" \
                   "1. **Sunlight Absorption**: Chlorophyll inside plant leaf cells absorbs solar light energy.\n" \
                   "2. **Water & Gas Intake**: Roots absorb water from soil, while leaf stomata absorb carbon dioxide from the air.\n" \
                   "3. **Food Production**: Solar energy converts water and carbon dioxide into glucose (sugar) for plant growth.\n" \
                   "4. **Oxygen Release**: Oxygen molecules are released back into the air as a natural byproduct.\n\n" \
                   "**Example**: A tree absorbing sunlight on a warm afternoon to make energy for growth while producing clean oxygen for animals and humans to breathe."

        # 2. Operating Systems
        if any(k in q_lower for k in ["virtual memory", "paging", "page fault", "tlb"]):
            return "Virtual memory separates physical RAM from a process's logical address space using fixed-size pages. When a requested page is not in RAM, a Page Fault exception triggers the OS kernel to load it from disk.\n\n" \
                   "### Key Components:\n" \
                   "1. **Paging System**: Memory is divided into fixed-size frames (RAM) and pages (disk).\n" \
                   "2. **Page Fault**: Interrupt raised when an address translation misses physical RAM.\n" \
                   "3. **TLB Hardware**: The Translation Lookaside Buffer caches recent address translations for high-speed CPU access.\n\n" \
                   "**Example**: Operating systems running multiple heavy applications simultaneously on limited physical RAM by dynamically swapping pages to disk."

        if any(k in q_lower for k in ["process", "thread", "context switch"]):
            return "A process is an isolated executing program with its own memory space, while a thread is a lightweight unit of execution within a process sharing its memory.\n\n" \
                   "### Key Differences:\n" \
                   "- **Memory Overhead**: Processes have independent memory heaps; threads share the parent process's memory.\n" \
                   "- **Context Switch Speed**: Switching between threads is much faster than switching between processes because virtual address spaces remain unchanged.\n\n" \
                   "**Example**: A web browser running as one process, with separate threads handling user interface clicks, audio playback, and network downloads."

        if any(k in q_lower for k in ["deadlock", "coffman", "banker"]):
            return "A deadlock occurs when two or more processes are blocked indefinitely, each waiting for resources held by the other.\n\n" \
                   "### The 4 Coffman Conditions:\n" \
                   "1. **Mutual Exclusion**: Resources cannot be shared simultaneously.\n" \
                   "2. **Hold and Wait**: Processes holding resources request new ones.\n" \
                   "3. **No Preemption**: Resources cannot be forcibly taken from a process.\n" \
                   "4. **Circular Wait**: A closed chain of processes each wait for resources held by the next.\n\n" \
                   "**Example**: Two processes where Process A holds Resource 1 and waits for Resource 2, while Process B holds Resource 2 and waits for Resource 1."

        # 3. Software Engineering
        if any(k in q_lower for k in ["solid", "design principle", "single responsibility", "liskov", "dependency inversion"]):
            return "The SOLID principles are five fundamental design guidelines that help developers write clean, maintainable, and scalable object-oriented software.\n\n" \
                   "### The 5 SOLID Principles:\n" \
                   "- **Single Responsibility**: A class should have only one reason to change.\n" \
                   "- **Open/Closed**: Software entities should be open for extension but closed for modification.\n" \
                   "- **Liskov Substitution**: Subtypes must be substitutable for their base types without breaking code.\n" \
                   "- **Interface Segregation**: Prefer small, specific interfaces over monolithic ones.\n" \
                   "- **Dependency Inversion**: Depend upon abstractions (interfaces) rather than concrete implementations.\n\n" \
                   "**Example**: Creating a payment interface so new gateways (PayPal, Stripe) can be added without modifying existing checkout code."

        if any(k in q_lower for k in ["design pattern", "factory", "singleton", "observer", "adapter"]):
            return "Design patterns are reusable, battle-tested solutions to common software architecture problems.\n\n" \
                   "### Main Categories:\n" \
                   "1. **Creational (e.g. Singleton, Factory)**: Manage object creation logic.\n" \
                   "2. **Structural (e.g. Adapter, Decorator)**: Compose classes and objects into larger structures.\n" \
                   "3. **Behavioral (e.g. Observer, Strategy)**: Coordinate communication and algorithm execution between objects.\n\n" \
                   "**Example**: The Observer pattern notifying all UI dashboard widgets automatically when new data arrives."

        # 4. DBMS
        if any(k in q_lower for k in ["dbms", "database", "2pl", "concurrency control", "acid", "sql", "transaction lock"]):
            return "Concurrency control in DBMS ensures that concurrent database transactions execute safely without causing data anomalies or corruption.\n\n" \
                   "### Two-Phase Locking (2PL) Protocol:\n" \
                   "1. **Growing Phase**: Transactions acquire locks as needed without releasing any.\n" \
                   "2. **Shrinking Phase**: Transactions release locks but cannot acquire new ones.\n" \
                   "3. **Strict 2PL**: Holds all exclusive write locks until transaction commit to prevent cascading aborts.\n\n" \
                   "**Example**: Banking applications using Strict 2PL so account balance updates are locked until confirmed, preventing double-spending."

        # 5. Computer Networks
        if any(k in q_lower for k in ["tcp", "udp"]):
            return "TCP (Transmission Control Protocol) and UDP (User Datagram Protocol) are transport layer protocols with different trade-offs between speed and reliability.\n\n" \
                   "### Key Comparison:\n" \
                   "- **TCP**: Connection-oriented, guarantees ordered packet delivery via 3-way handshakes and error checking.\n" \
                   "- **UDP**: Connectionless, lightweight protocol optimized for high speed and minimal latency without delivery guarantees.\n\n" \
                   "**Example**: Webpages (HTTP/HTTPS) and emails use TCP for accuracy; live video streaming and gaming use UDP for speed."

        if any(k in q_lower for k in ["osi", "layer", "router", "switch", "mac address"]):
            return "The OSI (Open Systems Interconnection) reference model standardizes network communications into 7 distinct functional layers.\n\n" \
                   "### The 7 Layers:\n" \
                   "1. **Physical**: Hardware cables and bit signals.\n" \
                   "2. **Data Link**: MAC addresses and frame transmission.\n" \
                   "3. **Network**: IP routing across subnets.\n" \
                   "4. **Transport**: Host-to-host communication (TCP/UDP).\n" \
                   "5. **Session**: Manages connection sessions.\n" \
                   "6. **Presentation**: Data formatting and encryption.\n" \
                   "7. **Application**: High-level network APIs (HTTP, DNS).\n\n" \
                   "**Example**: Web browsers operating at Layer 7 using HTTP, depending on Layer 4 TCP to transmit data across Layer 3 IP networks."

        # 6. Mathematics
        if any(k in q_lower for k in ["matrix", "linear algebra", "vector", "calculus", "derivative", "integral"]):
            return "Linear algebra and matrix operations form the mathematical foundation for computer graphics, spatial transformations, and machine learning models.\n\n" \
                   "### Core Concepts:\n" \
                   "- **Vectors**: Quantities possessing both magnitude and direction in N-dimensional space.\n" \
                   "- **Matrix Multiplication**: Row-by-column inner products that transform coordinate vectors from one space to another.\n" \
                   "- **Calculus**: Derivatives measure rates of change (e.g. gradient descent), while integrals sum continuous values.\n\n" \
                   "**Example**: 3D video games multiplying 4x4 matrices by 3D mesh vectors to render 3D game models onto 2D screens."

        # 7. Programming
        if any(k in q_lower for k in ["python", "gil", "async", "data structure", "algorithm", "array", "tree", "graph"]):
            return "Programming fundamentals involve choosing optimal data structures and algorithmic approaches to solve computational problems efficiently.\n\n" \
                   "### Key Concepts:\n" \
                   "- **Data Structures**: Arrays & Hash Tables offer fast O(1) lookup, while Trees & Graphs model hierarchical and networked relationships.\n" \
                   "- **Python GIL & Async**: Python's Global Interpreter Lock coordinates single-thread bytecode execution, while AsyncIO enables non-blocking I/O tasks.\n\n" \
                   "**Example**: Using a Hash Table to search million-user user accounts in milliseconds instead of scanning an unsorted array."

        # 8. Open-Ended General Knowledge Fallback
        import re
        clean_q = re.sub(r'^(STUDENT QUESTION:|Explain|What is|What are|Describe|How does|Tell me about)\s*', '', user_input, flags=re.IGNORECASE).strip(' "?.\'')
        topic_title = clean_q.title() if clean_q else "Study Concept"

        return f"**{topic_title}** refers to key principles and functional mechanisms within this topic area.\n\n" \
               f"### Key Concepts & Workflow:\n" \
               f"1. **Core Principle**: Fundamental rules and operational definitions governing **{topic_title}**.\n" \
               f"2. **Primary Mechanism**: Step-by-step processing and interactions between core components.\n" \
               f"3. **Practical Application**: Applying **{topic_title}** to solve real-world problems efficiently.\n\n" \
               f"**Example**: A real-world scenario demonstrating **{topic_title}** principles in action."

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
