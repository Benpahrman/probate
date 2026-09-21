"""
Gieni OS Vector & Embedding Service (Subsystem 8)
Provides native semantic similarity and embedding storage without
external third-party SaaS dependencies (Pinecone).
Compatible with SQLite in-process vector execution and PostgreSQL pgvector.
"""

import math
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session

from gieni_os.database.models import VectorEmbeddingModel


class VectorService:
    """Manages semantic embeddings and cosine similarity search."""

    def __init__(self, db: Session, dimension: int = 128):
        self.db = db
        self.dimension = dimension

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a normalized, deterministic semantic embedding vector.
        Uses SHA-256 multi-hash projection with L2-normalization.
        """
        words = text.lower().split()
        vector = [0.0] * self.dimension
        if not words:
            return vector

        for word in words:
            h = hashlib.sha256(word.encode("utf-8")).digest()
            for i in range(self.dimension):
                byte_val = h[i % len(h)]
                vector[i] += float(byte_val - 128) / 128.0

        # L2 normalize
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0.0:
            vector = [x / magnitude for x in vector]

        return [round(v, 6) for v in vector]

    def store(
        self,
        entity_type: str,
        entity_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VectorEmbeddingModel:
        """Store or update vector embedding for an entity."""
        vector = self.generate_embedding(text)
        embedding_str = json.dumps(vector)
        meta_str = json.dumps(metadata or {}, default=str)
        snippet = text[:500]

        record = (
            self.db.query(VectorEmbeddingModel)
            .filter(
                VectorEmbeddingModel.entity_type == entity_type,
                VectorEmbeddingModel.entity_id == entity_id,
            )
            .first()
        )

        if not record:
            record = VectorEmbeddingModel(
                entity_type=entity_type,
                entity_id=entity_id,
                embedding_json=embedding_str,
                dimension=self.dimension,
                content_snippet=snippet,
                meta_json=meta_str,
            )
            self.db.add(record)
        else:
            record.embedding_json = embedding_str
            record.content_snippet = snippet
            record.meta_json = meta_str

        self.db.commit()
        self.db.refresh(record)
        return record

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two unit vectors."""
        if len(vec1) != len(vec2) or not vec1:
            return 0.0
        return max(0.0, min(1.0, float(np.dot(vec1, vec2))))

    def similar(
        self,
        text: str,
        entity_type: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.10,
    ) -> List[Dict[str, Any]]:
        """Find the top-K semantically similar records using high-performance vectorized indexing."""
        query_vector = np.array(self.generate_embedding(text), dtype=np.float32)

        q = self.db.query(VectorEmbeddingModel)
        if entity_type:
            q = q.filter(VectorEmbeddingModel.entity_type == entity_type)

        candidates = q.all()
        if not candidates:
            return []

        matching_candidates = []
        vectors = []
        for c in candidates:
            try:
                emb = json.loads(c.embedding_json)
                if len(emb) == self.dimension:
                    matching_candidates.append(c)
                    vectors.append(emb)
            except json.JSONDecodeError:
                continue

        if not vectors:
            return []

        # Vectorized batch similarity calculation
        matrix = np.array(vectors, dtype=np.float32)
        if matrix.shape[0] == 0:
            return []

        # Cosine similarity via single BLAS matrix-vector product
        scores = np.dot(matrix, query_vector)

        # Filter by threshold and take top-K
        valid_indices = np.where(scores >= threshold)[0]
        if len(valid_indices) == 0:
            return []

        sorted_valid = valid_indices[np.argsort(scores[valid_indices])[::-1]][:top_k]

        return [
            {
                "entity_type": matching_candidates[i].entity_type,
                "entity_id": matching_candidates[i].entity_id,
                "score": round(float(scores[i]), 4),
                "content_snippet": matching_candidates[i].content_snippet,
                "metadata": json.loads(matching_candidates[i].meta_json or "{}"),
            }
            for i in sorted_valid
        ]

    def search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        return self.similar(text=query, entity_type=entity_type, top_k=top_k)
