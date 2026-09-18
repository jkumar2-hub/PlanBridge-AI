"""Matching module initialization."""
from .confidence_scorer import ConfidenceScorer
from .embedding_engine import EmbeddingEngine
from .fuzzy_matcher import FuzzyMatcher

__all__ = ["ConfidenceScorer", "EmbeddingEngine", "FuzzyMatcher"]
