import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = logging.getLogger("voicestudy.memory")

class QdrantMemoryService:
    def __init__(self):
        self.collection_name = os.getenv("QDRANT_COLLECTION", "study_memories")
        self.storage_path = os.getenv("QDRANT_STORAGE_PATH", "./qdrant_data")
        self.vector_size = 1536  # Default size for OpenAI text-embedding-3-small / gpt embeddings
        self.client = None
        self.storage_mode = "unknown"
        self._initialize_client()

    def _initialize_client(self):
        qdrant_url = os.getenv("QDRANT_URL", "").strip()
        qdrant_api_key = os.getenv("QDRANT_API_KEY", "").strip()

        try:
            if qdrant_url == ":memory:":
                logger.info("Initializing in-memory Qdrant client")
                self.client = QdrantClient(":memory:")
                self.storage_mode = "in_memory"
            elif qdrant_url and (qdrant_url.startswith("http://") or qdrant_url.startswith("https://")):
                if qdrant_api_key:
                    logger.info(f"Connecting to Qdrant Cloud at {qdrant_url}")
                    self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
                else:
                    logger.info(f"Connecting to local/remote Qdrant server at {qdrant_url}")
                    self.client = QdrantClient(url=qdrant_url)
                self.storage_mode = f"remote_server ({qdrant_url})"
            else:
                logger.info(f"Initializing persistent local disk Qdrant store at path='{self.storage_path}'")
                os.makedirs(self.storage_path, exist_ok=True)
                self.client = QdrantClient(path=self.storage_path)
                self.storage_mode = f"persistent_local ({self.storage_path})"

            self.init_collection()
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant (URL='{qdrant_url}', path='{self.storage_path}'), falling back to :memory:: {e}")
            self.client = QdrantClient(":memory:")
            self.storage_mode = "in_memory_fallback"
            self.init_collection()

    def _ensure_active_client(self):
        """Ensure active Qdrant client connection, re-opening if closed."""
        try:
            if self.client is None:
                self._initialize_client()
            elif hasattr(self.client, "_client") and getattr(self.client._client, "closed", False):
                self._initialize_client()
        except Exception:
            self._initialize_client()

    def get_matching_subjects(self, filter_subject: Optional[str]) -> List[str]:
        """Find stored subject variants matching the given filter (case-insensitive & substring)."""
        if not filter_subject or filter_subject.strip().lower() in ["all", ""]:
            return []
        target = filter_subject.strip().lower()
        stats = self.get_stats()
        known = stats.get("subjects_list", [])
        matched = []
        for s in known:
            s_lower = s.lower()
            if s_lower == target or target in s_lower or s_lower in target:
                matched.append(s)
        if not matched and not known:
            matched.append(filter_subject.strip())
        return matched

    def init_collection(self):
        """Ensure Qdrant collection exists with proper vector config."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")

    def _create_vector_fallback(self, text: str) -> List[float]:
        """
        Generate a deterministic 1536-dim normalized vector representation
        if OpenAI embedding key is not set or fails.
        """
        import hashlib
        import math
        
        vec = [0.0] * self.vector_size
        words = text.lower().split()
        for idx, word in enumerate(words):
            h = hashlib.sha256(word.encode()).hexdigest()
            # Map hash chunks to vector indices
            pos = int(h[:8], 16) % self.vector_size
            val = (int(h[8:12], 16) / 65535.0) * 2.0 - 1.0
            vec[pos] += val * (1.0 / (idx + 1.0))
        
        # Normalize vector
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        else:
            vec[0] = 1.0
        return vec

    def generate_embedding(self, text: str) -> List[float]:
        """Generate text embeddings using OpenAI API if available, else fallback."""
        llm_api_key = (os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
        if llm_api_key and llm_api_key.startswith("sk-") and len(llm_api_key) > 20:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=llm_api_key)
                response = client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                logger.info(f"[MEMORY] Embedding created via OpenAI text-embedding-3-small (dim={len(response.data[0].embedding)})")
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI Embedding API call failed, using vector fallback: {e}")
        
        vec = self._create_vector_fallback(text)
        logger.info(f"[MEMORY] Embedding created via Offline Vector Fallback (SHA-256 Hash Engine, dim={len(vec)}) - Set OPENAI_API_KEY for genuine OpenAI embeddings.")
        return vec

    def save_memory(
        self,
        text: str,
        subject: str = "General",
        topic: str = "Study Topic",
        memory_type: str = "voice_note",
        uid: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save a study memory to Qdrant vector database."""
        self._ensure_active_client()
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        vector = self.generate_embedding(text)
        
        user_uid = uid or (metadata.get("uid") if metadata else None) or "default_omi_user"
        
        payload = {
            "id": memory_id,
            "text": text,
            "content": text,
            "subject": subject,
            "topic": topic,
            "memory_type": memory_type,
            "uid": user_uid,
            "created_at": timestamp,
            "timestamp": timestamp,
            "date_display": datetime.now().strftime("%b %d, %Y"),
            **(metadata or {})
        }

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        
        logger.info(f"[QDRANT] Memory stored: id={memory_id} [uid={user_uid}] - Subject: {subject}, Topic: {topic}")
        return payload

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        subject_filter: Optional[str] = None,
        uid_filter: Optional[str] = None,
        min_score: float = 0.18
    ) -> List[Dict[str, Any]]:
        """Search Qdrant for semantically relevant study memories with subject and uid filtering and relevance thresholds."""
        self._ensure_active_client()
        query_clean = (query or "").strip()
        if not query_clean:
            return []

        clean_sub = subject_filter.strip() if (subject_filter and subject_filter.strip().lower() not in ["all", ""]) else None
        
        # If a specific subject is requested, resolve matching subject names
        matching_subjects = self.get_matching_subjects(clean_sub) if clean_sub else []
        if clean_sub and not matching_subjects:
            # The user asked for a subject that does not exist in memories -> clear empty state!
            logger.info(f"[QDRANT] Subject filter '{clean_sub}' matched no known subjects in store. Returning empty list.")
            return []

        query_vector = self.generate_embedding(query_clean)
        
        must_conditions = []
        if matching_subjects:
            if len(matching_subjects) == 1:
                must_conditions.append(
                    models.FieldCondition(
                        key="subject",
                        match=models.MatchValue(value=matching_subjects[0])
                    )
                )
            else:
                must_conditions.append(
                    models.FieldCondition(
                        key="subject",
                        match=models.MatchAny(any=matching_subjects)
                    )
                )

        if uid_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="uid",
                    match=models.MatchValue(value=uid_filter)
                )
            )

        qdrant_filter = models.Filter(must=must_conditions) if must_conditions else None

        try:
            fetch_limit = max(limit * 3, 10)
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=qdrant_filter,
                    limit=fetch_limit
                )
                results = res.points if hasattr(res, "points") else res
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=fetch_limit
                )
            else:
                results = []
            
            # Extract query tokens for keyword relevance checks
            import re
            from backend.agents.assistant_agent import STOP_WORDS
            q_tokens = set(re.findall(r'\b\w{3,}\b', query_clean.lower())) - STOP_WORDS

            memories = []
            for point in results:
                payload = dict(point.payload)
                score = round(float(point.score), 4)
                payload["score"] = score

                # Strict UID isolation check
                if uid_filter and payload.get("uid") != uid_filter:
                    continue

                # Subject filter check
                p_sub = (payload.get("subject") or "").strip()
                if clean_sub:
                    if not any(
                        m_sub.lower() == p_sub.lower() or clean_sub.lower() in p_sub.lower() or p_sub.lower() in clean_sub.lower()
                        for m_sub in matching_subjects
                    ):
                        continue

                # Relevance threshold check:
                p_text = (payload.get("text") or "").lower()
                p_topic = (payload.get("topic") or "").lower()
                p_sub_lower = p_sub.lower()

                has_kw_match = False
                if q_tokens:
                    has_kw_match = any(t in p_text or t in p_topic or t in p_sub_lower for t in q_tokens)

                # If no keywords match, require strong vector similarity to avoid unrelated memory leakage
                if not has_kw_match:
                    if score < 0.35:
                        continue
                else:
                    # If keywords match, accept unless similarity is essentially zero
                    if score < 0.05:
                        continue

                memories.append(payload)
                if len(memories) >= limit:
                    break

            logger.info(f"[QDRANT] Memories retrieved: {len(memories)} relevant matches for query '{query_clean[:60]}' [uid_filter={uid_filter}, subject_filter={clean_sub}]")
            return memories
        except Exception as e:
            logger.error(f"[QDRANT] Qdrant search failed: {e}")
            if "closed" in str(e).lower():
                self._initialize_client()
            return []

    def search_memory(self, query: str, limit: int = 5, subject_filter: Optional[str] = None, uid_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Alias for search_memories."""
        return self.search_memories(query, limit, subject_filter, uid_filter)

    def get_all_memories(
        self,
        limit: int = 50,
        uid_filter: Optional[str] = None,
        subject_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored study memories with optional uid and subject filtering."""
        self._ensure_active_client()
        clean_sub = subject_filter.strip() if (subject_filter and subject_filter.strip().lower() not in ["all", ""]) else None
        matching_subjects = self.get_matching_subjects(clean_sub) if clean_sub else []

        if clean_sub and not matching_subjects:
            return []

        try:
            must_conditions = []
            if uid_filter:
                must_conditions.append(
                    models.FieldCondition(
                        key="uid",
                        match=models.MatchValue(value=uid_filter)
                    )
                )
            if matching_subjects:
                if len(matching_subjects) == 1:
                    must_conditions.append(
                        models.FieldCondition(
                            key="subject",
                            match=models.MatchValue(value=matching_subjects[0])
                        )
                    )
                else:
                    must_conditions.append(
                        models.FieldCondition(
                            key="subject",
                            match=models.MatchAny(any=matching_subjects)
                        )
                    )

            scroll_filter = models.Filter(must=must_conditions) if must_conditions else None

            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=limit * 2 if clean_sub else limit,
                with_payload=True,
                with_vectors=False
            )
            memories = [dict(r.payload) for r in records]

            # Post-filters for safety
            if uid_filter:
                memories = [m for m in memories if m.get("uid") == uid_filter]
            if clean_sub:
                memories = [
                    m for m in memories
                    if any(
                        ms.lower() == (m.get("subject") or "").lower() or
                        clean_sub.lower() in (m.get("subject") or "").lower() or
                        (m.get("subject") or "").lower() in clean_sub.lower()
                        for ms in matching_subjects
                    )
                ]

            # Sort by created_at descending
            memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return memories[:limit]
        except Exception as e:
            logger.error(f"Failed to scroll Qdrant memories: {e}")
            if "closed" in str(e).lower():
                self._initialize_client()
            return []

    def get_recent_memories(self, limit: int = 20, uid_filter: Optional[str] = None, subject_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Alias for get_all_memories."""
        return self.get_all_memories(limit=limit, uid_filter=uid_filter, subject_filter=subject_filter)

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a study memory by ID."""
        self._ensure_active_client()
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[memory_id])
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            if "closed" in str(e).lower():
                self._initialize_client()
            return False

    def get_stats(self, uid_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics with optional uid filtering."""
        self._ensure_active_client()
        memories = self.get_all_memories(limit=1000, uid_filter=uid_filter)
        subjects = set(m.get("subject", "General") for m in memories if m.get("subject"))
        topics = set(m.get("topic", "General") for m in memories if m.get("topic"))
        
        return {
            "total_memories": len(memories),
            "total_subjects": len(subjects),
            "total_topics": len(topics),
            "subjects_list": sorted(list(subjects)),
            "topics_list": sorted(list(topics)),
            "storage_mode": self.storage_mode,
            "storage_path": self.storage_path,
            "vector_dimension": self.vector_size
        }

# Global memory service instance
memory_service = QdrantMemoryService()

