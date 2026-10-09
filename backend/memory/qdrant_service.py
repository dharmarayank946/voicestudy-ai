import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
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
        memory_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
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
        uid_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search Qdrant for semantically relevant study memories with optional subject and uid filtering."""
        query_vector = self.generate_embedding(query)
        
        must_conditions = []
        if subject_filter and subject_filter != "All":
            must_conditions.append(
                models.FieldCondition(
                    key="subject",
                    match=models.MatchValue(value=subject_filter)
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
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=qdrant_filter,
                    limit=limit
                )
                results = res.points if hasattr(res, "points") else res
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=limit
                )
            else:
                results = []
            
            memories = []
            for point in results:
                payload = dict(point.payload)
                payload["score"] = round(float(point.score), 4)
                memories.append(payload)

            logger.info(f"[QDRANT] Memories retrieved: {len(memories)} relevant matches for query '{query[:60]}' [uid_filter={uid_filter}]")
            return memories
        except Exception as e:
            logger.error(f"[QDRANT] Qdrant search failed: {e}")
            return []

    def search_memory(self, query: str, limit: int = 5, subject_filter: Optional[str] = None, uid_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Alias for search_memories."""
        return self.search_memories(query, limit, subject_filter, uid_filter)

    def get_all_memories(self, limit: int = 50, uid_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve stored study memories with optional uid filtering."""
        try:
            scroll_filter = None
            if uid_filter:
                scroll_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="uid",
                            match=models.MatchValue(value=uid_filter)
                        )
                    ]
                )

            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            memories = [dict(r.payload) for r in records]
            # Sort by created_at descending
            memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return memories
        except Exception as e:
            logger.error(f"Failed to scroll Qdrant memories: {e}")
            return []

    def get_recent_memories(self, limit: int = 20, uid_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Alias for get_all_memories."""
        return self.get_all_memories(limit=limit, uid_filter=uid_filter)

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a study memory by ID."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[memory_id])
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            points_count = collection_info.points_count
        except Exception:
            points_count = 0
            
        memories = self.get_all_memories(limit=100)
        subjects = set(m.get("subject", "General") for m in memories)
        topics = set(m.get("topic", "General") for m in memories)
        
        return {
            "total_memories": points_count,
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

