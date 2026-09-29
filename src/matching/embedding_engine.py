"""Embedding Engine using sentence-transformers (all-MiniLM-L6-v2) and RapidFuzz."""
from typing import Any, Dict, List, Optional
import numpy as np
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer


class EmbeddingEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.activity_cache: List[Dict[str, Any]] = []
        self.activity_embeddings: Optional[np.ndarray] = None

    def index_activities(self, activities: List[Dict[str, Any]]) -> None:
        """Encodes all schedule activities into embeddings for cosine matching."""
        self.activity_cache = activities
        texts = [
            f"{act['name']} | Discipline: {act['discipline']} | Location: {act['location']}"
            for act in activities
        ]
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        self.activity_embeddings = embeddings

    def compute_semantic_scores(self, query_text: str) -> List[float]:
        """Computes cosine similarity of query against all indexed activities."""
        if self.activity_embeddings is None or not self.activity_cache:
            return []

        query_emb = self.model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)[0]
        # Dot product with normalized embeddings equals cosine similarity
        similarities = np.dot(self.activity_embeddings, query_emb)
        return [float(max(0.0, s)) for s in similarities]

    def compute_lexical_score(self, query_text: str, candidate_text: str) -> float:
        """RapidFuzz token set ratio normalized between 0.0 and 1.0."""
        return float(fuzz.token_set_ratio(query_text, candidate_text) / 100.0)
